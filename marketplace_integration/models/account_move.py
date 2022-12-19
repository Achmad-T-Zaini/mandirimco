# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from collections import defaultdict
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import ast
import json
import re
import warnings

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        old_vals = vals_list
        if any('state' in vals and vals.get('state') == 'posted' for vals in vals_list):
            raise UserError(_('You cannot create a move already in the posted state. Please create a draft move and post it after.'))

        vals_list = self._move_autocomplete_invoice_lines_create_new(vals_list)
#        raise UserError(_('CP old_vals %s\nnew %s')%(old_vals, vals_list,))
        rslt = super(AccountMove, self).create(vals_list)
        for i, vals in enumerate(vals_list):
            if 'line_ids' in vals:
                rslt[i].update_lines_tax_exigibility()
        return rslt

    @api.model
    def _move_autocomplete_invoice_lines_create_new(self, vals_list):
        ''' During the create of an account.move with only 'invoice_line_ids' set and not 'line_ids', this method is called
        to auto compute accounting lines of the invoice. In that case, accounts will be retrieved and taxes, cash rounding
        and payment terms will be computed. At the end, the values will contains all accounting lines in 'line_ids'
        and the moves should be balanced.

        :param vals_list:   The list of values passed to the 'create' method.
        :return:            Modified list of values.
        '''
        old_vals = vals_list
        new_vals_list = []
        for vals in vals_list:
            vals = dict(vals)

            if vals.get('invoice_date') and not vals.get('date'):
                vals['date'] = vals['invoice_date']

            default_move_type = vals.get('move_type') or self._context.get('default_move_type')
            ctx_vals = {}
            if default_move_type:
                ctx_vals['default_move_type'] = default_move_type
            if vals.get('journal_id'):
                ctx_vals['default_journal_id'] = vals['journal_id']
                # reorder the companies in the context so that the company of the journal
                # (which will be the company of the move) is the main one, ensuring all
                # property fields are read with the correct company
                journal_company = self.env['account.journal'].browse(vals['journal_id']).company_id
                allowed_companies = self._context.get('allowed_company_ids', journal_company.ids)
                reordered_companies = sorted(allowed_companies, key=lambda cid: cid != journal_company.id)
                ctx_vals['allowed_company_ids'] = reordered_companies
            self_ctx = self.with_context(**ctx_vals)
            vals = self_ctx._add_missing_default_values(vals)

            is_invoice = vals.get('move_type') in self.get_invoice_types(include_receipts=True)

            if 'line_ids' in vals:
                vals.pop('invoice_line_ids', None)
                new_vals_list.append(vals)
                continue

            if is_invoice and 'invoice_line_ids' in vals:
                vals['line_ids'] = vals['invoice_line_ids']

            vals.pop('invoice_line_ids', None)

            move = self_ctx.new(vals)
            new_vals_list.append(move._move_autocomplete_invoice_lines_values_new())

            cek_aml = []
            for line in move.line_ids:
                cek_aml.append({'COA': line.account_id.id,
                                    'root': line.account_id.root_id.id,
                                    'name': line.name,
                                    'account': line.account_id.name,
                                    'debit': line.debit,
                                    'credit': line.credit,
                                    })
#            raise UserError(_('aml %s')%(cek_aml,))
#            raise UserError(_('CP is_invoice %s\nold_vals %s\n\n new %s\nnew_vals_list %s')%(is_invoice,old_vals, vals,new_vals_list,))

        return new_vals_list

    def _move_autocomplete_invoice_lines_values_new(self):
        ''' This method recomputes dynamic lines on the current journal entry that include taxes, cash rounding
        and payment terms lines.
        '''
        self.ensure_one()

        for line in self.line_ids:
            analytic_account = line._cache.get('analytic_account_id')

            # Do something only on invoice lines.
            if line.exclude_from_invoice_tab:
                continue

            # Shortcut to load the demo data.
            # Doing line.account_id triggers a default_get(['account_id']) that could returns a result.
            # A section / note must not have an account_id set.
            if not line._cache.get('account_id') and not line.display_type and not line._origin:
                line.account_id = line._get_computed_account() or self.journal_id.default_account_id
            if line.product_id and not line._cache.get('name'):
                line.name = line._get_computed_name()

            # Compute the account before the partner_id
            # In case account_followup is installed
            # Setting the partner will get the account_id in cache
            # If the account_id is not in cache, it will trigger the default value
            # Which is wrong in some case
            # It's better to set the account_id before the partner_id
            # Ensure related fields are well copied.
            if line.partner_id != self.partner_id.commercial_partner_id:
                line.partner_id = self.partner_id.commercial_partner_id
            line.date = self.date
            line.recompute_tax_line = True
            line.currency_id = self.currency_id
            if analytic_account:
                line.analytic_account_id = analytic_account


        self.line_ids._onchange_price_subtotal()
        self._recompute_dynamic_lines(recompute_all_taxes=True)
        cek_aml = []
        for line in self.line_ids:
            cek_aml.append({'COA': line.account_id.id,
                                    'root': line.account_id.root_id.id,
                                    'name': line.name,
                                    'account': line.account_id.name,
                                    'debit': line.debit,
                                    'credit': line.credit,
                                    })
#        raise UserError(_('aml %s')%(cek_aml,))

        values = self._convert_to_write(self._cache)
        values.pop('invoice_line_ids', None)
        return values

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        ACCOUNTING_FIELDS = ('debit', 'credit', 'amount_currency')
        BUSINESS_FIELDS = ('price_unit', 'quantity', 'discount', 'tax_ids')

        for vals in vals_list:
            move = self.env['account.move'].browse(vals['move_id'])
            vals.setdefault('company_currency_id', move.company_id.currency_id.id) # important to bypass the ORM limitation where monetary fields are not rounded; more info in the commit message

            # Ensure balance == amount_currency in case of missing currency or same currency as the one from the
            # company.
            currency_id = vals.get('currency_id') or move.company_id.currency_id.id
            if currency_id == move.company_id.currency_id.id:
                balance = vals.get('debit', 0.0) - vals.get('credit', 0.0)
                vals.update({
                    'currency_id': currency_id,
                    'amount_currency': balance,
                })
            else:
                vals['amount_currency'] = vals.get('amount_currency', 0.0)

            if move.is_invoice(include_receipts=True):
                currency = move.currency_id
                partner = self.env['res.partner'].browse(vals.get('partner_id'))
                taxes = self.new({'tax_ids': vals.get('tax_ids', [])}).tax_ids
                tax_ids = set(taxes.ids)
                taxes = self.env['account.tax'].browse(tax_ids)

                # Ensure consistency between accounting & business fields.
                # As we can't express such synchronization as computed fields without cycling, we need to do it both
                # in onchange and in create/write. So, if something changed in accounting [resp. business] fields,
                # business [resp. accounting] fields are recomputed.
                if any(vals.get(field) for field in ACCOUNTING_FIELDS):
                    price_subtotal = self._get_price_total_and_subtotal_model(
                        vals.get('price_unit', 0.0),
                        vals.get('quantity', 0.0),
                        vals.get('discount', 0.0),
                        currency,
                        self.env['product.product'].browse(vals.get('product_id')),
                        partner,
                        taxes,
                        move.move_type,
                    ).get('price_subtotal', 0.0)
                    vals.update(self._get_fields_onchange_balance_model(
                        vals.get('quantity', 0.0),
                        vals.get('discount', 0.0),
                        vals['amount_currency'],
                        move.move_type,
                        currency,
                        taxes,
                        price_subtotal
                    ))
                    vals.update(self._get_price_total_and_subtotal_model(
                        vals.get('price_unit', 0.0),
                        vals.get('quantity', 0.0),
                        vals.get('discount', 0.0),
                        currency,
                        self.env['product.product'].browse(vals.get('product_id')),
                        partner,
                        taxes,
                        move.move_type,
                    ))
                elif any(vals.get(field) for field in BUSINESS_FIELDS):
                    vals.update(self._get_price_total_and_subtotal_model(
                        vals.get('price_unit', 0.0),
                        vals.get('quantity', 0.0),
                        vals.get('discount', 0.0),
                        currency,
                        self.env['product.product'].browse(vals.get('product_id')),
                        partner,
                        taxes,
                        move.move_type,
                    ))
                    vals.update(self._get_fields_onchange_subtotal_model(
                        vals['price_subtotal'],
                        move.move_type,
                        currency,
                        move.company_id,
                        move.date,
                    ))

        lines = super(AccountMoveLine, self).create(vals_list)

        moves = lines.mapped('move_id')
        if self._context.get('check_move_validity', True):
            moves._check_balanced()
        moves._check_fiscalyear_lock_date()
        lines._check_tax_lock_date()
        moves._synchronize_business_models({'line_ids'})

        return lines
