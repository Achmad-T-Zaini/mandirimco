# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class ResCompany(models.Model):
    _inherit = 'res.company'

    account_laba_ditahan = fields.Many2one('account.account',string='Account P/L', domain = lambda self:[('user_type_id', '=', 11)])

class AccountUpdateLockDate(models.TransientModel):
    _name = 'account.lock.date'
    _description = 'Lock date for accounting'

    company_id = fields.Many2one(comodel_name='res.company', string="Company",
                                 required=True)
    period_lock_date = fields.Date(string="Lock Date for Non-Advisers",
                                   help="Only users with the 'Adviser' role can edit accounts prior to "
                                        "and inclusive of this date. Use it for period locking inside an "
                                        "open fiscal year, for example.")
    fiscalyear_lock_date = fields.Date(string="Lock Date",
                                       help="No users, including Advisers, can edit accounts prior to and "
                                            "inclusive of this date. Use it for fiscal year locking for "
                                            "example.")
    tax_lock_date = fields.Date("Tax Lock Date", help="No users can edit journal entries related to a tax prior "
                                                      "and inclusive of this date.")

    @api.model
    def default_get(self, field_list):
        res = super(AccountUpdateLockDate, self).default_get(field_list)
        company = self.env.company
        res.update({
            'company_id': company.id,
            'period_lock_date': company.period_lock_date,
            'fiscalyear_lock_date': company.fiscalyear_lock_date,
            'tax_lock_date': company.tax_lock_date,
        })
        return res

    def _check_execute_allowed(self):
        self.ensure_one()
        has_adviser_group = self.env.user.has_group(
            'account.group_account_manager')
        if not (has_adviser_group or self.env.uid == SUPERUSER_ID):
            raise UserError(_("You are not allowed to execute this action."))

    def execute(self):
        self.ensure_one()
        self._check_execute_allowed()

        company = self.company_id
        if (company.fiscalyear_lock_date and
                self.fiscalyear_lock_date < company.fiscalyear_lock_date):
            raise UserError(
                _("You cannot set the Fiscal Year Lock date in the past.")
            )
        # Then check if unposted moves are present before the date
        moves = self.env['account.move'].search(
            [('company_id', '=', company.id),
             ('date', '<=', self.fiscalyear_lock_date),
             ('state', '=', 'draft')])
        if moves:
            raise UserError(
                _("You cannot set the permanent lock date since entries are "
                  "still unposted before this date.")
            )

        temp_lock_date = False
        if self.fiscalyear_lock_date and relativedelta(self.fiscalyear_lock_date,company.fiscalyear_lock_date).years==1:
            result = self.create_retain_earning()
            if result:
                self.company_id.sudo().write({
                    'period_lock_date': self.period_lock_date,
                    'fiscalyear_lock_date': self.fiscalyear_lock_date,
                    'tax_lock_date': self.tax_lock_date,
                    })
        elif self.period_lock_date:
            self.company_id.sudo().write({
                    'period_lock_date': self.period_lock_date,
                    'tax_lock_date': self.tax_lock_date,
                    })

        return {'type': 'ir.actions.act_window_close'}


    def create_retain_earning(self):
        self.ensure_one()
        account_type = self.env.ref('account.data_unaffected_earnings')
        unaffected_earnings_account = self.env['account.account'].search(
            [
                ('user_type_id', '=', account_type.id),
                ('company_id', '=', self.company_id.id)
            ])

        vals = {
                    'date_from': self.fiscalyear_lock_date + relativedelta(years=-1,days=1),
                    'date_to': self.fiscalyear_lock_date,
                    'target_move': 'posted',
                    'account_report_id': 1,
                    'date_range': False,
            }
        report_pl = self.env['ins.financial.report'].create(vals)

        data_pl = report_pl.get_report_values()
        laba_tahun_berjalan = data_pl['report_lines'][0]['balance']
#        raise UserError(_('LABA TAHUN BERJALAN %s')%(laba_tahun_berjalan,))
        self.create_move(unaffected_earnings_account,laba_tahun_berjalan)
        
        return True

    def create_move(self,account_id,amount):
        '''
        Validasi dan Posting LABA TAHUN BERJALAN
        '''
        AccountMove = self.env['account.move']
        journal_id = self.env['account.journal'].search([('code', '=', 'MISC')],limit=1)
        tanggal = self.fiscalyear_lock_date + relativedelta(days=1)
#        name = journal_id.sequence_id.with_context(ir_sequence_date=tanggal).next_by_id()

        move_lines = []
        # Create debit line
        line_vals = {
                    'name': account_id.name,
                    'debit': amount if amount>0 else 0.0,
                    'credit': amount*-1 if amount<0 else 0.0,
                    'account_id': account_id.id,
                    'journal_id': journal_id.id,
#                    'partner_id': self.partner_id.id,
                    'date': tanggal,
                    'date_maturity': tanggal,
                    'ref': account_id.name,
                }
        move_lines.append((0, 0, line_vals))

        # Create credit line
        account_credit_id = self.company_id.account_laba_ditahan
        credit_vals = {
                    'name': account_credit_id.name,
                    'debit': amount*-1 if amount<0 else 0.0,
                    'credit': amount if amount>0 else 0.0,
                    'account_id': account_credit_id.id,
                    'journal_id': journal_id.id,
#                    'partner_id': self.partner_id.id,
                    'date': tanggal,
                    'date_maturity': tanggal,
                    'ref': account_id.name,
                }
        move_lines.append((0, 0, credit_vals))

        # First, create the move
        move_vals = {
#                'name': name,
                'journal_id': journal_id.id,
                'company_id': self.company_id.id,
                'date': tanggal,
                'narration': 'LABA TAHUN BERJALAN',
                'ref': '',
                'line_ids': move_lines,
            }
#        raise UserError(_('move_lines %s')%(move_vals))
        move = AccountMove.create(move_vals)
        move.post()
        return 
