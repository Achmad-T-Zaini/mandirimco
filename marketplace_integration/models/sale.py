# -*- coding: utf-8 -*-
# Part of Akun+. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import json
import requests

class MarketPlace(models.Model):
    _name = "marketplace.overview"
    _description = "MarketPlace Overview/Configuration"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string='MarketPlace', copy=False, store=True, related='partner_id.name')
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True, default=_default_currency)
    journal_id = fields.Many2one('account.journal', string='Payment Journal', copy=False, store=True)
    partner_id = fields.Many2one('res.partner',string='Partner', copy=False, store=True)
    notes = fields.Text('Description', copy=False, store=False)
    new_order = fields.Integer('New Order', compute='_compute_order',copy=False, store=False)
    finish_order = fields.Integer('Finish Order', compute='_compute_order', copy=False, store=False)
    cancel_order = fields.Integer('Cancel Order', compute='_compute_order', copy=False, store=False)
    deliver_order = fields.Integer('Deliver Order', compute='_compute_order', copy=False, store=False)
    balance = fields.Monetary(string='Balance', compute='_compute_order', currency_field='currency_id', copy=False )
    template_data = fields.Selection([
            ('tokopedia','Tokopedia'),
            ('shopee','Shopee'),
        ], string='Template CSV', index=True, required=True)
    toped_lines = fields.One2many('tokopedia.order','mp_id', string="Tokopedia Lines", copy=False)

    @api.depends('toped_lines','toped_lines.status_order')
    def _compute_order(self):
        for rec in self:
            new_order = finish_order = cancel_order = deliver_order =  0
            for line in rec.toped_lines:
                if line.status_order=='Pesanan Baru':
                    new_order +=1
                elif line.status_order=='Pesanan Selesai':
                    finish_order +=1
                elif line.status_order=='Pesanan Dikirim':
                    deliver_order +=1
                elif line.status_order=='Pesanan Tiba':
                    deliver_order +=1
                else:
                    cancel_order +=1
            deposit = self.env['tokopedia.deposit'].search([('id','!=',False)], limit=1)
            if deposit:
                saldo = deposit.balance
            else:
                saldo=0.0

            rec.update({'new_order': new_order, 'finish_order': finish_order,
                        'deliver_order': deliver_order, 'cancel_order': cancel_order,
                        'balance': saldo})

class SaleOrder(models.Model):
    _inherit = "sale.order"

    kurir = fields.Selection([
        ('tiki', 'Titipan Kilat'),
        ('pos', 'POS Indonesia'),
        ('jne', 'Jalur Nugraha Ekakurir - JNE'),
        ], string='Courier', readonly=True, copy=False, index=True)
    origin = fields.Many2one('rajaongkir.kota', string='Kota Asal', copy=False)
    destination = fields.Many2one('rajaongkir.kota', string='Kota Tujuan', copy=False)
    weight = fields.Integer(string='Estimasi Berat', default=1)
    jenis_kurir = fields.One2many('kurir.jenis', 'order_id',  string='Jenis Kurir' )
    estimasi_waktu = fields.Char(string='Estimasi Waktu', copy=False)
    estimasi_harga = fields.Monetary(string='Estimasi Harga', currency_field='currency_id', copy=False, default=0.0 )

    @api.onchange('kurir','origin','destination','weight')
    def _onchange_kurir(self):
        self.ensure_one()
        if self.kurir and self.origin and self.destination and self.weight>0:
            res = self.cek_ongkir()


    def cek_ongkir(self):
        url = "https://api.rajaongkir.com/starter/cost"

        payload  ='origin=' + str(self.origin.id) + '&destination=' + str(self.destination.id) 
        payload += '&weight=' + str(self.weight) + '&courier=' + self.kurir
        headers = {
                    'Key': '75650a35280cdf8aaf66d3c58a3bab61',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }

        response = json.loads(requests.request("POST", url, headers=headers, data=payload).text)
        res = response['rajaongkir']['status']['code']
        self.update({'jenis_kurir': False,})
        jenis_kurir = []
        if res==200:
            results = response['rajaongkir']['results'][0]['costs']
            for jenis in results:
                jenis_kurir += [(0,0,{'name': jenis['service'] + ' - ' + jenis['description'],
                                  'order_id': self.id,
                                  'estimasi_waktu': jenis['cost'][0]['etd'] ,
                                  'estimasi_harga': jenis['cost'][0]['value'],
                                      })]
#            raise UserError(_('response %s')%(jenis_kurir,))
        else:
            raise UserError(_('response %s')%(response,))

        self.update({'jenis_kurir': jenis_kurir,})

class KurirJenis(models.Model):
    _name = "kurir.jenis"
    _description = "Jenis Kurir MarketPlace"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string='Jenis', copy = False)
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True, default=_default_currency)
    estimasi_waktu = fields.Char(string='Estimasi Waktu', copy=False)
    estimasi_harga = fields.Monetary(string='Estimasi Harga', currency_field='currency_id', copy=False, default=0.0 )
    order_id = fields.Many2one('sale.order', string='Order ID', ondelete='cascade')

    def update_ongkir(self):
        self.ensure_one()
        self.order_id.estimasi_harga = self.estimasi_harga
        self.order_id.estimasi_waktu = self.estimasi_waktu
#        raise UserError(_('dt %s - %s')%(self.name,self.estimasi_harga))
        return

