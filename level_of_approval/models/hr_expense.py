# -*- coding: utf-8 -*-
# Part of Akun+. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Company")
    ], default='own_account', tracking=True, readonly=False, states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]}, string="Paid By")
    loa_type = fields.Many2one('level_of_approval', string='Purchase Type', domain=[("type", "=", "purchase")],index=True, required=True)
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


    @api.onchange('employee_id','total_amount','loa_type')
    def _check_loa(self):
        for rec in self:
            if rec.employee_id:
                req_employee = self.env['hr.employee'].search([('user_id','=',rec.employee_id.user_id.id)])
                rec.approver1 = req_employee.parent_id.user_id.id

                if rec.loa_type:
                    loa = self.env['level_of_approval.line'].search([('loa_id','=',rec.loa_type.id),
                                                                 ('from_amount','<',rec.total_amount),
                                                                 ('amount','>=',rec.total_amount),
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

    def button_approved(self):
        if self.is_approver:
            self.write({"loa_a1": True})
        elif self.is_final_approver:
            self.write({"loa_a2": True})

        if self.loa_a1 and self.loa_a2:
            self.write({"state": "approve"})
        elif self.loa_a1 and not self.approver2:
            self.write({"state": "approve"})
        return 

    def button_draft(self):
        self.write({'state': 'draft', 'loa_a1': False, 'loa_a2': False})
        return {}

    def action_sheet_move_create(self):
        samples = self.mapped('expense_line_ids.sample')
        if samples.count(True):
            if samples.count(False):
                raise UserError(_("You can't mix sample expenses and regular ones"))
            self.write({'state': 'post'})
            return

        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.company.currency_id).rounding))
        res = expense_line_ids.action_move_create()
        for sheet in self.filtered(lambda s: not s.accounting_date):
            sheet.accounting_date = sheet.account_move_id.date
        to_post = self.filtered(lambda sheet: sheet.payment_mode == 'own_account' and sheet.expense_line_ids)
#        raise UserError(_('to_post %s')%(to_post,))
        to_post.write({'state': 'post'})
#        (self - to_post).write({'state': 'done'})
        self.activity_update()
        return res
