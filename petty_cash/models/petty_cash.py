# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from datetime import datetime, timedelta, date

class PettyCash(models.Model):
    _name = "petty.cash"
    _inherit = ['mail.thread']
    _description = "Petty Cash Management"
    _order = "request_date"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string='Deskripsi', store=True,copy=False)
    user_id = fields.Many2one('res.users', string='Request By',store=True, copy=False)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=True, copy=False)
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True, default=_default_currency)
    kas_debit = fields.Monetary(currency_field='currency_id', compute='_compute_total_kas', string='Kas Debit', store=True, copy=False)
    kas_credit = fields.Monetary(currency_field='currency_id', compute='_compute_total_kas', string='Kas Credit', store=True, copy=False)
    kas_balance = fields.Monetary(currency_field='currency_id', compute='_compute_total_kas', string='Kas Balance', store=True, copy=False)
    debit_lines = fields.One2many('petty.cash.debit','kas_id', string='Cash In / Out')
    credit_lines = fields.One2many('petty.cash.credit','kas_id', string='Expenses')
    journal_id = fields.Many2one('account.journal', string='Journal',store=True)
    request_date = fields.Date(string='Request Date', default=datetime.today())
    
    @api.depends('debit_lines', 'debit_lines.state', 'credit_lines', 'credit_lines.state')
    def _compute_total_kas(self):
        for rec in self:
            total_debit = total_credit = total_balance = 0.0
            for line in rec.debit_lines:
#                raise UserError(_('state %s - %s')%(line.state,line.amount))
                if line.state=='paid' or line.state=='done':
                    total_debit += line.amount
                elif not line.state:
                    line.write({'state': 'draft'})
            for line in rec.credit_lines:
                if line.state=='approve':
                    total_credit += line.price_total
            total_balance = total_debit - total_credit

            rec.update({'kas_debit': total_debit, 'kas_credit': total_credit, 'kas_balance': total_balance})

    @api.onchange('debit_lines')
    def _onchange_debit_lines(self):
        for line in self.debit_lines:
            if not line.state:
                line.write({'state': 'draft'})


class PettyCashDebit(models.Model):
    _name = "petty.cash.debit"
    _inherit = ['mail.thread']
    _description = "Debit Petty Cash"
    _order = "tanggal"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    @api.model
    def _get_default_loa_type(self):
        loa_type = self.env['level_of_approval'].search([('type','=','pettycash')],order='id',limit=1)
        return loa_type.id

    name = fields.Char(string='Deskripsi', store=True, copy=False)
    number = fields.Char(string='Number', store=True, copy=False, readonly=True)
    tanggal = fields.Date(string='Date', default=datetime.today())
    kas_id = fields.Many2one('petty.cash',string='Kas ID')
    user_id = fields.Many2one('res.users', string='Request By',store=True, copy=False, related='kas_id.user_id')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', related='kas_id.analytic_account_id')
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True, default=_default_currency)
    amount = fields.Monetary(currency_field='currency_id', string='Amount')
    invoice_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False, readonly=True)
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('posted', 'Posted'),
        ('paid', 'Paid'),
        ('done', 'Done'),
        ('refused', 'Refused')
        ], string='Status', copy=False, index=True,  store=True,default='draft',compute='_compute_inv_state',
        help="Status of Petty Cash")
    loa_type = fields.Many2one('level_of_approval', string='Purchase Type', default=_get_default_loa_type,domain=[("type", "=", "purchase")],index=True, required=True, copy=False)
    loa_a1 = fields.Boolean(default=False, copy=False)
    loa_a2 = fields.Boolean(default=False, copy=False)
    approver1 = fields.Many2one('res.users', string='Approver', copy=False)
    approver2 = fields.Many2one('res.users', string='Final Approver', copy=False)
    is_approver = fields.Boolean(
        string="Is Approver", compute="_compute_is_approver", readonly=True, copy=False
    )
    is_final_approver = fields.Boolean(
        string="Is Final Approver", compute="_compute_is_approver", readonly=True, copy=False
    )
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='own_account', tracking=True, states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]}, string="Paid By")
    payment_id = fields.Many2one('account.payment', string='Payment Entry', readonly=True,copy=False)

    @api.depends()
    def _compute_is_approver(self):
        if self.approver1.id==self.env.uid:
            self.is_approver = True
        else:
            self.is_approver = False

        if self.approver2.id==self.env.uid:
            self.is_final_approver = True
        else:
            self.is_final_approver = False


    @api.onchange('user_id','amount','loa_type')
    def _check_loa(self):
        for rec in self:
            if rec.user_id:
                req_employee = self.env['hr.employee'].search([('user_id','=',rec.user_id.id)])
                rec.approver1 = req_employee.parent_id.user_id.id

                if rec.loa_type:
                    loa = self.env['level_of_approval.line'].search([('loa_id','=',rec.loa_type.id),
                                                                 ('from_amount','<',rec.amount),
                                                                 ('amount','>=',rec.amount),
                                                                 ])
#                    raise UserError(_('loa %s == %s \n %s')%(rec.loa_type.id,rec.amount_total,loa ))

                    if loa :
                        if req_employee.job_id.job_level>loa.requestor:
                            raise UserError(_('Maximum amount limit Reached'))

                        parent_id = req_employee
                        while parent_id:
                            if parent_id.job_id.job_level<=loa.appr1:
                                rec.approver1 = parent_id.user_id.id
                                parent_id = False
                            else:
                                parent_id = parent_id.parent_id

                        if loa.appr2:
                            parent_id = req_employee
                            while parent_id:
                                if parent_id.job_id.job_level<=loa.appr2:
                                    rec.approver2 = parent_id.user_id.id
                                    parent_id = False
                                else:
                                    parent_id = parent_id.parent_id
                        else:
                            rec.approver2 = False
                    else:
                        rec.approver1 = False
                        rec.approver2 = False
#                        raise UserError(_('Purchase Type did not Configure Properly'))
        return

    def button_to_approve(self):
        return self.write({"state": "to_approve"})

    def button_approved(self):
        if self.is_approver:
            self.write({"loa_a1": True})
        elif self.is_final_approver:
            self.write({"loa_a2": True})

        if self.loa_a1 and self.loa_a2:
            self.write({"state": "approved"})
        elif self.loa_a1 and not self.approver2:
            self.write({"state": "approved"})
        return 

    @api.depends('invoice_id.payment_state')
    def _compute_inv_state(self):
        if self.invoice_id and self.invoice_id.payment_state=='paid':
            self.update({'state': 'paid'})
        elif self.invoice_id :
            self.update({'state': 'posted'})

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.invoice_id.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def _get_number(self):
        rekno = self.env['ir.sequence'].next_by_code('PCR')
        if not rekno:
            cr_seq = self.env['ir.sequence'].create({
                            'name': 'Petty Cash Payment',
                            'code': 'PCR',
                            'implementation': 'standard',
                            'active': True,
                            'prefix': 'PCR/%(year)s/%(month)s/',
                            'padding': 5,
                            'company_id': self.env.user.company_id.id,
                            'use_date_range': False,
                            })
            if cr_seq:
                rekno = self.env['ir.sequence'].next_by_code('PCR')
            else:
                raise UserError('Sequence Error')
        return rekno

    def button_confirm(self):
#    def action_create_invoice(self):
        move_group_by_sheet = self._get_account_move_by_sheet()

        move_line_values_by_expense = self._get_account_move_line_values()

        for rec in self:
            # get the account move of the related sheet
            move = move_group_by_sheet[rec.id]

            # get move line values
            move_line_values = move_line_values_by_expense.get(rec.id)

            # link move lines to move, and move to expense sheet
            move.write({'line_ids': [(0, 0, line) for line in move_line_values]})
            rec.write({'number': self._get_number(),'invoice_id': move.id})

#            if expense.payment_mode == 'company_account':
#                expense.sheet_id.paid_expense_sheets()

        # post the moves
        for move in move_group_by_sheet.values():
            move._post()

        return move_group_by_sheet

    def _get_account_move_by_sheet(self):
        """ Return a mapping between the expense sheet of current expense and its account move
            :returns dict where key is a sheet id, and value is an account move record
        """
        move_grouped_by_sheet = {}
        move_vals = self._prepare_move_values()
        move = self.env['account.move'].with_context(default_journal_id=move_vals['journal_id']).create(move_vals)
        move_grouped_by_sheet[self.id] = move
        return move_grouped_by_sheet

    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal = self.kas_id.journal_id
        account_date = self.tanggal
        move_values = {
            'journal_id': journal.id,
            'company_id': self.env.user.company_id.id,
            'date': account_date,
            'ref': self.name,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
        }
        return move_values

    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for rec in self:
            move_line_name = rec.user_id.partner_id.name + ': ' + rec.name.split('\n')[0][:64]
            account_src = rec.loa_type.credit_account_id
            account_dst = rec.loa_type.debit_account_id
            account_date = rec.tanggal or fields.Date.context_today(rec)

            company_currency = self.currency_id

            move_line_values = []
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = rec.user_id.partner_id.id

            # source move line
            balance = -rec.amount
            amount_currency = balance
            move_line_src = {
                'name': move_line_name,
                'quantity': 1,
                'debit': 0,
                'credit': -balance if balance < 0 else 0,
                'amount_currency': amount_currency,
                'account_id': account_src.id,
#                'product_id': rec.loa_type.product_id.id,
#                'product_uom_id': rec.loa_type.product_uom.id,
                'analytic_account_id': rec.kas_id.analytic_account_id.id,
#                'analytic_tag_ids': [(6, 0, rec.analytic_tag_ids.ids)],
                'pettycash_id': rec.id,
                'partner_id': partner_id,
#                'tax_ids': [(6, 0, expense.tax_ids.ids)],
#                'tax_tag_ids': [(6, 0, taxes['base_tags'])],
                'currency_id': rec.currency_id.id,
            }
            move_line_values.append(move_line_src)
            total_amount -= balance
            total_amount_currency -= move_line_src['amount_currency']

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': 0,
                'account_id': account_dst.id,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency,
                'currency_id': rec.currency_id.id,
                'pettycash_id': rec.id,
                'partner_id': partner_id,
            }
            move_line_values.append(move_line_dst)

            move_line_values_by_expense[rec.id] = move_line_values
        return move_line_values_by_expense


class PettyCashCredit(models.Model):
    _name = "petty.cash.credit"
    _inherit = ['mail.thread']
    _description = "Credit Petty Cash"
    _order = "tanggal"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string='Deskripsi', store=True, copy=False)
    tanggal = fields.Date(string='Date', default=datetime.today())
    kas_id = fields.Many2one('petty.cash',string='Kas ID')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', related='kas_id.analytic_account_id')
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True, default=_default_currency)
    product_id = fields.Many2one('product.product', string='Product', domain = lambda self:[('available_in_pos', '=', False),'|',('can_be_expensed', '=', True),('purchase_ok', '=', True)], required=True,store=True)
    quantity = fields.Float(string='Quantity',
        required=True, default=1, store=True)
    price_unit = fields.Monetary(currency_field='currency_id', string='Unit Price', required=True, default=0, store=True, copy=False)
    price_total = fields.Monetary(currency_field='currency_id', string='Total', compute='_compute_total', store=True)
    move_id = fields.Many2one('account.move', string='Move Expense',readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('done', 'Done'),
        ('refused', 'Refused')
        ], string='Status', copy=False, index=True,  store=True,default='draft',
        help="Status of PettyCash.")
    binary_expense = fields.Binary(string="Expense File")
    file_expense = fields.Char(string="File Name")
    kas_balance = fields.Monetary(currency_field='currency_id', string='Kas Balance', store=True, copy=False, related='kas_id.kas_balance')


    @api.depends('quantity','price_unit','product_id')
    def _compute_total(self):
        if self.product_id and not self.product_id.property_account_expense_id and not self.product_id.categ_id.property_account_expense_categ_id:
            raise UserError(_('this Product does not have Account Expense'))
        if self.quantity and self.price_unit:
            self.price_total = self.quantity * self.price_unit

    def action_submit(self):
#        raise UserError(_('CP %s')%(self.price_total<=self.kas_id.kas_balance))
        if self.kas_id.kas_balance>=self.price_total:
            self.write({'state': 'submit'})
        else:
            raise UserError(_('Requested Expenses Exceed Balance'))

    def action_refuse(self):
        self.write({'state': 'refused'})

    def action_approve(self):
        if self.price_total>0 and self.kas_id.kas_balance>=self.price_total:
            expense_account = False
            if self.product_id.property_account_expense_id:
                expense_account = self.product_id.property_account_expense_id
            else:
                expense_account = self.product_id.categ_id.property_account_expense_categ_id
             
            aml = [(0, 0, self._prepare_move_line_kas_expense(self.kas_id.journal_id.payment_credit_account_id,0,self.price_total))]
            aml += [(0, 0, self._prepare_move_line_kas_expense(expense_account,self.price_total,0))]

            move_vals = {
                    'ref': self.kas_id.name + ' - ' + self.name,
                    'line_ids': aml,
                    'journal_id': self.kas_id.journal_id.id,
                    'date': self.tanggal,
                    'narration': self.name,
                    }

            raise UserError(_('aml %s')%(move_vals,))

            move = self.env['account.move'].create(move_vals)
            move.post()

            self.write({'state': 'approve', 'move_id': move.id})
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                }

    def _prepare_move_line_kas_expense(self,coa,db_amount,cr_amount):
        return {
            'date_maturity': self.tanggal, 
            'partner_id': self.kas_id.user_id.employee_id.address_home_id.id or False,
            'name': coa.name,
            'debit': db_amount, 
            'credit': cr_amount, 
            'balance': db_amount - cr_amount,
            'debit_cash_basis': db_amount, 
            'credit_cash_basis': cr_amount, 
            'balance_cash_basis': db_amount - cr_amount, 
            'account_id': coa.id, 
            'quantity': 1.0, 
            'product_id': self.product_id.id, 
            'journal_id': self.kas_id.journal_id.id,
            'analytic_account_id': self.analytic_account_id.id,
        }
