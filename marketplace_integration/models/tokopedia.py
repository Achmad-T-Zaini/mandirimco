# -*- coding: utf-8 -*-
# Part of Akun+. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class TokopediaOrder(models.Model):
    _name = "tokopedia.order"
    _description = "Order MarketPlace Tokopedia"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string='Nomor Invoice', copy=False, store=True)
    mp_id = fields.Many2one('marketplace.overview', string="Marketplace", readonly=True, copy=False)
    tokopedia_line = fields.One2many('tokopedia.order.line','tokopedia_id', string="Order Lines", copy=False)
    deposit_line = fields.One2many('tokopedia.deposit','tokopedia_id', string="Deposit Lines", copy=False)
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True, default=_default_currency)
    tanggal_pembayaran = fields.Datetime(string='Tanggal Pembayaran', copy=False, store=True)
    status_order = fields.Char(string='Status Terakhir', copy=False, store=True)
    tanggal_selesai = fields.Datetime(string='Tanggal Selesai', copy=False, store=True)
    tanggal_batal = fields.Datetime(string='Tanggal Dibatalkan', copy=False, store=True)
    tanggal_kirim = fields.Datetime(string='Tanggal Kirim', copy=False, store=True)
    biaya_kirim = fields.Monetary(string='Biaya Pengiriman', currency_field='currency_id', copy=False, default=0.0 )
    biaya_asuransi = fields.Monetary(string='Biaya Asuransi', currency_field='currency_id', copy=False, default=0.0 )
    total_biaya_kirim = fields.Monetary(string='Total Biaya Pengiriman', currency_field='currency_id', copy=False, default=0.0 )
    total_penjualan = fields.Monetary(string='Total Penjualan', currency_field='currency_id', copy=False, default=0.0 )
    total_potongan = fields.Monetary(string='Total Potongan', compute='_compute_total', currency_field='currency_id', copy=False, default=0.0 )
    total_net = fields.Monetary(string='Total Diterima', compute='_compute_total', currency_field='currency_id', copy=False, default=0.0 )
    nama_pembeli = fields.Char(string='Nama Pembeli', copy=False, store=True)
    telp_pembeli = fields.Char(string='Telp Pembeli', copy=False, store=True)
    nama_penerima = fields.Char(string='Nama Penerima', copy=False, store=True)
    telp_penerima = fields.Char(string='Telp Penerima', copy=False, store=True)
    alamat_penerima = fields.Text(string='Alamat Penerima', copy=False, store=True)
    kota_penerima = fields.Char(string='Kota Penerima', copy=False, store=True)
    prov_penerima = fields.Char(string='Provinsi Penerima', copy=False, store=True)
    nama_kurir = fields.Char(string='Kurir', copy=False, store=True)
    type_kurir = fields.Char(string='Type Pengiriman', copy=False, store=True)
    resi_kurir = fields.Char(string='No Resi/Booking', copy=False, store=True)
    nama_campaign = fields.Char(string='Nama Campaign', copy=False, store=True)
    cod = fields.Char(string='COD', copy=False, store=True)
    order_ref = fields.Char(string='Order Reff', readonly=True,copy=False, store=True)

    @api.depends('deposit_line')
    def _compute_total(self):
        for rec in self:
            total_potong = self.total_penjualan
            for line in rec.deposit_line:
                total_potong -= line.nominal

            if rec.status_order == 'Pesanan Selesai':
                rec.update({'total_potongan': total_potong, 'total_net': self.total_penjualan-total_potong,})
            else:
                rec.update({'total_potongan': 0, 'total_net': 0,})


class TokopediaOrderLine(models.Model):
    _name = "tokopedia.order.line"
    _description = "Order Line MarketPlace Tokopedia"

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string='Nomor Invoice', copy=False, store=True)
    tokopedia_id = fields.Many2one('tokopedia.order',  string='Tokopedia ID', ondelete='cascade', readonly=True, copy=False)
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True, default=_default_currency)
    nama_produk = fields.Char(string='Nama Produk', copy=False, store=True)
    product_id = fields.Many2one('product.product',string='Product',  copy=False, store=True)
    kode_sku = fields.Char(string='SKU', copy=False)
    catatan_pembeli = fields.Char(string='Catatan Pembeli', copy=False)
    catatan_penjual = fields.Char(string='Catatan Penjual', copy=False)
    product_qty = fields.Float(string='Qty', copy=False)
    harga_awal = fields.Monetary(string='Harga Awal', currency_field='currency_id', copy=False, default=0.0 )
    harga_setelah_diskon = fields.Monetary(string='Harga Setelah Diskon', currency_field='currency_id', copy=False, default=0.0 )
    harga_jual = fields.Monetary(string='Unit Price', currency_field='currency_id', copy=False, default=0.0 )
    total = fields.Monetary(string='Total', compute='_compute_total',currency_field='currency_id', copy=False, default=0.0 )
    subsidi_tokopedia = fields.Monetary(string='Subsidi Tokopedia', currency_field='currency_id', copy=False, default=0.0 )
    voucher_toko_terpakai = fields.Monetary(string='Voucher Toko Terpakai', currency_field='currency_id', copy=False, default=0.0 )
    jenis_voucher = fields.Char(string='Jenis Voucher', copy=False, store=True)
    kode_voucher = fields.Char(string='Kode Voucher', copy=False, store=True)

    @api.depends('product_qty','harga_jual')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.product_qty * rec.harga_jual


class TokopediaDeposit(models.Model):
    _name = "tokopedia.deposit"
    _description = "Deposit MarketPlace Tokopedia"
    _order = 'tanggal desc'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string='Description', copy=False, store=True)
    tanggal = fields.Datetime(string='Tanggal', copy=False, store=True)
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True, default=_default_currency)
    nominal = fields.Monetary(string='Nominal', currency_field='currency_id', copy=False, default=0.0 )
    balance = fields.Monetary(string='Balance', currency_field='currency_id', copy=False, default=0.0 )
    tokopedia_id = fields.Many2one('tokopedia.order',  string='Tokopedia ID', ondelete='cascade', readonly=True, copy=False)
