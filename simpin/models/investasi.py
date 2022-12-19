# -*- coding: utf-8 -*-
# Part of Akun+. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta, date

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class SimPinInvestasi(models.Model):
    _name = "simpin.investasi"
    _description = "Investasi Anggota Simpin"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string='Nomor Sertifikat', default='/', store=True, copy=False)
    member_id = fields.Many2one('simpin.member',string='Nama Anggota', required=True,store=True, copy=False,
                                 domain=[('state', '=', 'done')])
    product_id = fields.Many2one('product.product',string='Product', required=True,
                              readonly=True, states={'draft': [('readonly', False)]}, copy=False, store=True,
                                 domain=[('is_simpin', '=', True),('jenis_simpin', '=', 'investasi')])
    currency_id = fields.Many2one('res.currency', string="Currency", default=_default_currency)
    account_analytic_id = fields.Many2one('account.analytic.account', required=True, string='Analytic Account')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('check', 'Check Document'),
        ('approve', 'Approved'),
        ('active', 'Active'),
        ('close', 'Closed'),
        ('block', 'Blocked'),
        ], string='Status', copy=False, index=True, default='draft', readonly=True, store=True)
    total_investasi = fields.Monetary(string='Total Investasi',currency_field='currency_id', store=True, copy=False)
    jangka_waktu = fields.Selection([
        ('1', '1 Bulan'),
        ('3', '3 Bulan'),
        ('6', '6 Bulan'),
        ('12','12 Bulan'),
        ('24','24 Bulan'),
        ('36','36 Bulan'),
        ], string='Jangka Waktu', copy=False, index=True, default='1',required=True, store=True)
    tanggal_akad = fields.Date(string='Tanggal Akad', default=date.today())
    jatuh_tempo = fields.Date(string='Jatuh Tempo',compute='_compute_jatuh_tempo',store=True)
    pengembalian  = fields.Selection([
        ('aro', 'Automatic Roll Over (ARO)'),
        ('jatuh_tempo', 'Jatuh Tempo'),
        ], string='Pengembalian', copy=False, index=True, default='aro')
    nisbah_investor = fields.Float(string='Margin Investor',default=25, required=True)
    pajak_nisbah = fields.Many2one('account.tax', string='Pajak', required=True, domain=[('type_tax_use','!=','none'),('active', '=', True)])
    ahli_waris_id = fields.Many2one('simpin.member.waris',string='Ahli Waris')
    bank_id = fields.Many2one('res.bank','Bank',help='Nama Bank Penerima')
    bank_norek = fields.Char('Account #',help='No Rekening Penerima')
    bank_namarek = fields.Char('Beneficiary',help='Nama Pada Rekening')
    journal_id = fields.Many2one('account.journal', string='Journal')
    move_investasi = fields.Many2one('account.move',readonly=True, store=True, string='Journal Setoran', copy=False )
    pembayaran_nisbah = fields.Selection([
        ('bulanan', 'Setiap Bulan'),
        ('jatuh_tempo', 'Jatuh Tempo'),
        ], string='Pembayaran Margin', copy=False, index=True, default=1)
    invoice_lines = fields.One2many('account.move', 'investasi_id', string='Margin', copy=False)


    @api.depends('jangka_waktu','tanggal_akad')
    def _compute_jatuh_tempo(self):
        self.jatuh_tempo = self.tanggal_akad + relativedelta(months=int(self.jangka_waktu))
        

    @api.onchange('member_id')
    def _onchange_member_id(self):
        t_domain = False
        if self.member_id:
            ahli_waris = self.env['simpin.member.waris'].search([
                                                      ('member_id', '=', self.member_id.id),
                                                          ])
            t_domain = {'domain': {'ahli_waris_id': [('id', 'in', ahli_waris.ids)]}}
        return t_domain


    def action_break(self):
        raise UserError('Action Break')

    def action_submit(self):
        self.write({'state': 'submit'})

    def action_check(self):
        self.write({'state': 'check'})

    def action_approve(self):
        raise UserError('Action Approve')

    def action_close(self):
        raise UserError(_('submodul Close'))
        self.write({'state': 'close'})

    def action_block(self):
        raise UserError(_('submodul Block'))
        self.write({'state': 'block'})


