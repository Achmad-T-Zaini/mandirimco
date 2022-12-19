# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.osv import expression


class ResPartner(models.Model):
#    _name = 'res.partner'
    _inherit = 'res.partner'


    member = fields.Boolean(string='Anggota', default=True)
    contact_person = fields.Many2one('res.partner',string='Contact Person', domain=[('parent_id','=','id')])
    nomor_induk = fields.Char(string="N I P")
    partner_position_id = fields.Many2one("res.partner.position",string="Position")
    company_group_id = fields.Many2one("res.partner.company.group",string="Company Group")


    @api.model
    def default_get(self, default_fields):
        """If we're creating a new account through a many2one, there are chances that we typed the account code
        instead of its name. In that case, switch both fields values.
        """
        default_name = self._context.get('default_name')
        default_nomor_induk = self._context.get('default_nomor_induk')
        if default_name and not default_nomor_induk:
            try:
                default_nomor_induk = int(default_name)
            except ValueError:
                pass
            if default_nomor_induk:
                default_name = False
        contextual_self = self.with_context(default_name=default_name, default_nomor_induk=default_nomor_induk)
        return super(ResPartner, contextual_self).default_get(default_fields)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        cek_sp = name.find(' - ')
        if name:
            if cek_sp>=0:
                domain = ['|', ('nomor_induk', '=ilike', name.split(' - ')[0] + '%'), ('name', operator, name)]
            else:
                domain = ['|', ('nomor_induk', '=ilike', name + '%'), ('name', operator, name)]

#            raise UserError(_('name %s = cek_sp %s \n domain %s')%(name,cek_sp,domain))                
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        partner_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(partner_ids).name_get()

    def name_get(self):
        result = []
        for member in self:
            if member.nomor_induk:
                name = member.nomor_induk + ' - ' + member.name
            else:
                name = 'New - ' + member.name
            result.append((member.id, name))
        return result


