# -*- coding: utf-8 -*-
# Part of Akun+. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.addons import decimal_precision as dp

from werkzeug.urls import url_encode
import psycopg2
from psycopg2 import DatabaseError, errorcodes
import psycopg2.extras

class ResPartner(models.Model):
    _inherit = "res.partner"

    nomor_induk = fields.Char(string="N I P")
    partner_position_id = fields.Many2one("res.partner.position",string="Position")
    company_group_id = fields.Many2one("res.partner.company.group",string="Company Group")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
                domain = ['|', ('nomor_induk', operator, name ), ('name', operator, name)]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    def name_get(self):
        result = []
    
        for rec in self:
            if rec.nomor_induk:
                result.append((rec.id, '%s - %s' % (rec.nomor_induk,rec.name)))
            else:
                result.append((rec.id, rec.name))
    
        return result

class PartnerPosition(models.Model):
    _name = "res.partner.position"
    _description = "Partner Position"

    name = fields.Char(string="Position")
    description = fields.Text(string="Description")


class PartnerCompanyGroup(models.Model):
    _name = "res.partner.company.group"
    _description = "Partner Company Group"

    name = fields.Char(string="Company Group")
    description = fields.Text(string="Description")

class MasterGeneral(models.Model):
    _name = "master.general"
    _description = "tabel umum"
    _inherit = ['mail.thread']
    _order = "type_umum"

    name = fields.Char(string='Deskripsi', copy=False,default=lambda self: _('Deskripsi'), required=True)
    type_umum = fields.Selection([
        ('agama', 'Agama'),
        ('identitas', 'Identitas'),
        ('gender', 'Jenis Kelamin'),
        ('marital', 'Status Perkawinan'),
        ('jabatan', 'Jabatan'),
        ('ahliwaris', 'Ahli Waris'),
        ('lain', 'Lainnya'),
        ], string='Type', copy=False, index=True, required=True)

class ProductTemplate(models.Model):
    _inherit = ['product.template']

    is_simpin = fields.Boolean(string='SimPin')
    jenis_simpin = fields.Selection([
        ('simpanan', 'Simpanan'),
        ('pinjaman', 'Pinjaman'),
        ('investasi', 'Investasi'),
        ('pembiayaan', 'Pembiayaan'),
        ], string='Jenis SimPin', copy=False, index=True, default='simpanan')
    minimal_setor = fields.Monetary(string='Minimal Setoran', currency_field='currency_id', default=10000)
    interest_lines = fields.One2many('master.interest','product_tmpl_id',string='Interest')
    pelunasan_lines = fields.One2many('master.pelunasan','product_tmpl_id',string='Kewajiban Pelunasan')
    biaya_lines = fields.One2many('master.biaya','product_tmpl_id',string='Komponen Biaya')
    coa_piutang = fields.Many2one('account.account', string='Account Piutang', copy=False)
    coa_piutang_margin = fields.Many2one('account.account', string='Account Piutang Interest', copy=False)
    coa_margin = fields.Many2one('account.account', string='Account Pendapatan', copy=False)

class MasterInterest(models.Model):
    _name = "master.interest"
    _description = "Master Interest"
    _order = "periode_max"


    name = fields.Char(string='Description', required=True, copy=False, index=True, default=lambda self: _('Default Interest'))
    product_tmpl_id = fields.Many2one('product.template',string='Product Template',required=True, ondelete="cascade")
    periode_min = fields.Integer(string='Periode Min(bulan)', copy=False, index=True, required=True, default=12)
    periode_max = fields.Integer(string='Periode Max(bulan)', copy=False, index=True, required=True, default=24)
    margin = fields.Float(string='Margin (%)', required=True, copy=False, default=15)
    nilai_min =  fields.Float(string='Nilai Min', required=True, copy=False, default=5000000)
    nilai_max =  fields.Float(string='Nilai Max', required=True, copy=False, default=20000000)

class MasterPelunasan(models.Model):
    _name = "master.pelunasan"
    _description = "Master Pelunasan"
    _order = "periode_max"


    name = fields.Char(string='Description', required=True, copy=False, index=True, default=lambda self: _('Pelunasan Tahun pertama'))
    product_tmpl_id = fields.Many2one('product.template',string='Product Template',required=True, ondelete="cascade")
    periode_min = fields.Integer(string='Periode Min(bulan)', copy=False, index=True, required=True, default=3)
    periode_max = fields.Integer(string='Periode Max(bulan)', copy=False, index=True, required=True, default=12)
    pelunasan = fields.Selection([
        ('0', 'Tanpa Kewajiban'),
        ('1', 'Bulan Berjalan'),
        ('2', 'Bulan Berjalan +1'),
        ('3', 'Bulan Berjalan +2'),
        ('4', 'Bulan Berjalan +3'),
        ], string='Kewajiban Pelunasan', copy=False, index=True, default='0')

class MasterBiaya(models.Model):
    _name = "master.biaya"
    _description = "Komponen Biaya Simpin"
#    _order = "tipe"

    name = fields.Char(string='Deskripsi', related='product_id.name')
    product_tmpl_id = fields.Many2one('product.template',string='Product Template')
    nilai_pct = fields.Float(default=0.0, string='Pct (%)')
    nominal = fields.Float(default=0.0, string='Nominal')
    product_id = fields.Many2one('product.product',string='Product', required=True, copy=False,
                                 domain=[('type', '=', 'service')])
    is_edit = fields.Boolean(string='Editable', default=False)
    is_bill = fields.Boolean(string='Billable', default=False)

