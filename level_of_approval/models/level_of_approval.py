# -*- coding: utf-8 -*-
# Part of Akun+. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import csv
import base64
import io

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_update_image(self):
        with open('/opt/odoo14_mco/odoo-custom-addons/wilayah/data/product_template_image.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
#                    raise UserError(_('Column names are %s')%(row))
                    line_count += 1
                else:
#                    raise UserError(_('barcode %s')%(row[1]))
                    barcode = str(row[1])
                    line_count += 1

                    if len(row[2])>0:
                        prod_template = self.env['product.template'].search([('barcode','=',barcode)])
                        dt_img = self.env['ir.attachment'].search([('res_id','=',prod_template.id),('res_model','=','product.template'),('res_field','=','image_1920')])
                        if dt_img:
                            raise UserError(_('Update Image %s')%(dt_img.id,))
                        else:
                            b64_img = base64.b64encode(row[2].encode('utf-8'))
                            attachment = self.env['ir.attachment'].create({'name': 'image_1920',
                                                                            'res_model': 'product.template',
                                                                            'res_field': 'image_1920',
                                                                            'res_id': prod_template.id,
                                                                            'company_id': 1,
                                                                            'type': 'binary',
                                                                            'store_fname': b64_img,
                                                                            })
#                            raise UserError(_('No Image %s == %s')%(prod_template.name,attachment.id,))
                            break

class Followers(models.Model):
    _inherit = 'mail.followers'

    @api.model
    def create(self, vals):
        if 'res_model' in vals and 'res_id' in vals and 'partner_id' in vals:
            dups = self.env['mail.followers'].search([('res_model', '=',vals.get('res_model')), ('res_id', '=', vals.get('res_id')), ('partner_id', '=', vals.get('partner_id'))])
            
            if len(dups):
                for p in dups:
                    p.unlink()
        
        res = super(Followers, self).create(vals)
        
        return res

class LevelOfApproval(models.Model):
    _name = "level_of_approval"
    _description = "Level of Approval"

    name = fields.Char(string='Level of Approval', required=True)
    type = fields.Selection([
            ('purchase','Purchase'),
            ('sale','Sales'),
            ('pettycash','Petty Cash'),
            ('cash_advance','Cash Advance'),
        ], string='Type LOA', index=True, default='purchase', required=True)
    note = fields.Text('Internal Notes')
    loa_line = fields.One2many('level_of_approval.line','loa_id', string="LOA Lines", copy=False)
    journal_id = fields.Many2one('account.journal', string='Journal',store=True, required=True)
    debit_account_id = fields.Many2one('account.account', string='Default Debit Account',store=True, required=True)
    credit_account_id = fields.Many2one('account.account', string='Default Credit Account',store=True, required=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    product_id = fields.Many2one('product.product', string='Product', domain=[('type', '=', 'service')], change_default=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')


    def action_update_pos(self):
        stm = self.env['stock.move'].search([('reference','like','%POS%'),
                                             ('date','>=','2022-01-03 00:00:00'),
                                             ('date','<=','2022-01-07 23:59:59'),
                                             ])
        if stm:
            for line in stm:
                stm_line = self.env['stock.move.line'].search([('reference','=',line.reference),
                                                     ('product_id','=',line.product_id.id)
                                                      ])
                if stm_line:
                    if len(stm_line)==1 and line.product_uom_qty==0:
                        line.write({'product_uom_qty': stm_line.qty_done})
                    elif len(stm_line)==1 and stm_line.qty_done == line.product_uom_qty:
                        stm_line.write({'move_id': line.id})
#                        raise UserError(_('Data %s : %s = %s:%s')%(stm_line.move_id.name,stm_line.qty_done,line.name,line.product_uom_qty))
                    else:
                        stot = 0
                        for stl in stm_line:
                            stot += stl.qty_done

                        if stot == line.product_uom_qty:
                            for stl in stm_line:
                                stl.write({'move_id': line.id})
                        else:
                            if line.product_uom_qty==0:
                                line.write({'product_uom_qty': stot})
                            else:
                                raise UserError(_('Data %s : %s = %s:%s')%(stm_line.move_id.name,stm_line.qty_done,line.name,line.product_uom_qty))
                else:
                    raise UserError(_('update Data %s:%s:%s \n %s:%s:%s')%(stm_line.move_id.id,stm_line.product_id.name,stm_line.qty_done,line.id,line.product_id.name,line.product_uom_qty))
 
class LevelOfApprovalLine(models.Model):
    _name = "level_of_approval.line"
    _description = "Level of Approval Line"

    name = fields.Char(string='Code', required=True,default='LOA')
    loa_id = fields.Many2one('level_of_approval',  string='LOA', readonly=True, copy=False)
    from_amount = fields.Float(string='From', store=True)
    amount = fields.Float(string='To Amount', store=True)
    requestor =  fields.Selection([
        ('1', 'President Director'),
        ('2', 'Director'),
        ('3', 'General Manager'),
        ('4', 'Manager'),
        ('5', 'Supervisor'),
        ('6', 'Team Leader'),
        ('7', 'Staff'),
            ], default=7, string='Requestor')
    appr1 = fields.Selection([
        ('1', 'President Director'),
        ('2', 'Director'),
        ('3', 'General Manager'),
        ('4', 'Manager'),
        ('5', 'Supervisor'),
        ('6', 'Team Leader'),
        ('7', 'Staff'),
            ], string='Approver 1')
    appr2 = fields.Selection([
        ('1', 'President Director'),
        ('2', 'Director'),
        ('3', 'General Manager'),
        ('4', 'Manager'),
        ('5', 'Supervisor'),
        ('6', 'Team Leader'),
        ('7', 'Staff'),
            ], string='Approver 2')


class Job(models.Model):
    _inherit = "hr.job"

    job_level = fields.Selection([
        ('1', 'President Director'),
        ('2', 'Director'),
        ('3', 'General Manager'),
        ('4', 'Manager'),
        ('5', 'Supervisor'),
        ('6', 'Team Leader'),
        ('7', 'Staff'),
        ], default='7')
