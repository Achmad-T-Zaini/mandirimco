# -*- coding: utf-8 -*-
# Part of Akun+. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _default_loa_sales(self):
        loa_sales = self.env['level_of_approval'].search([('type','=','sale')],limit=1)
        return loa_sales.id


    state = fields.Selection(selection_add=[
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ])

    loa_type = fields.Many2one('level_of_approval', string='Sales Type', domain=[("type", "=", "sale")],index=True, required=True, copy=False, default=_default_loa_sales)
    approver1 = fields.Many2one('res.users', string='Approver', copy=False)
    approver2 = fields.Many2one('res.users', string='Final Approver', copy=False)
    loa_a1 = fields.Boolean(default=False, copy=False)
    loa_a2 = fields.Boolean(default=False, copy=False)
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


    @api.onchange('user_id','amount_total','loa_type')
    def _check_loa(self):
        for rec in self:
            if rec.user_id:
                req_employee = self.env['hr.employee'].search([('user_id','=',rec.user_id.id)])
                rec.approver1 = req_employee.parent_id.user_id.id
                
                if rec.loa_type:
                    loa = self.env['level_of_approval.line'].search([('loa_id','=',rec.loa_type.id),
                                                                 ('from_amount','<',rec.amount_total),
                                                                 ('amount','>=',rec.amount_total),
                                                                 ])
                    if loa:
                        if req_employee.job_id and req_employee.job_id.job_level and req_employee.job_id.job_level>loa.requestor:
                            raise UserError(_('Maximum amount limit Reached'))
                        elif not req_employee.job_id:
                            raise UserError(_('Requestor %s has no Valid Job Level')%(rec.user_id.name))

                        parent_id = req_employee
                        if req_employee.parent_id.job_id.job_level>=req_employee.job_id.job_level:
                            raise UserError(_('Manager %s, should has Greater Job Level than Employee %s')%(req_employee.parent_id.name, req_employee.name,))

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
        if self.is_final_approver:
            self.write({"loa_a2": True})

        if self.loa_a1 and self.loa_a2:
            self.write({"state": "approved"})
        elif self.loa_a1 and not self.approver2:
            self.write({"state": "approved"})
        return 

    def button_draft(self):
        self.mapped("line_ids").do_uncancel()
        return self.write({"state": "draft", "loa_a1": False, "loa_a2": False})

    def button_to_approve(self):
        return self.write({"state": "to_approve"})

