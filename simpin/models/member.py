# -*- coding: utf-8 -*-
# Part of Akun+. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta, date
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from werkzeug.urls import url_encode
import re
import psycopg2
from psycopg2 import DatabaseError, errorcodes
import psycopg2.extras
import json
import base64




class SimPinMember(models.Model):
    _name = "simpin.member"
    _description = "Keanggotaan Simpin"
    _inherit = ['mail.thread']

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id


    name = fields.Char(string='Name', required=True, copy=False, index=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
        copy=False, default=lambda self: self.env['res.company']._company_default_get())
    partner_id = fields.Many2one('res.partner', string='Partner')
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True, default=_default_currency)
    nomor_anggota = fields.Char(string='Nomor Anggota', readonly=True, store=True)
    address = fields.Char(string='Alamat')
    rukun_tetangga = fields.Char(string='RT')
    rukun_warga = fields.Char(string='RW')
    kelurahan_id = fields.Many2one('wilayah.kelurahan',string='Kelurahan')
    kecamatan_id = fields.Many2one('wilayah.kecamatan',string='Kecamatan')
    kabkota_id = fields.Many2one('wilayah.kabkota',string='Kab / Kota')
    provinsi_id = fields.Many2one('wilayah.provinsi',string='Provinsi')
    kodepos =  fields.Char(string='Kodepos',store=True)
    tempat_lahir = fields.Char(string='Tempat Lahir')
    tanggal_lahir = fields.Date(string='Tanggal Lahir')
    type_identitas = fields.Many2one('master.general', string='Type Identitas', 
                                     domain=[('type_umum', '=', 'identitas')])
    agama = fields.Many2one('master.general', string='Agama', 
                                     domain=[('type_umum', '=', 'agama')])
    gender = fields.Many2one('master.general', string='Jenis Kelamin', 
                                     domain=[('type_umum', '=', 'gender')])
    marital = fields.Many2one('master.general', string='Status Perkawinan', 
                                     domain=[('type_umum', '=', 'marital')])
    jabatan = fields.Many2one('master.general', string='Jabatan', 
                                     domain=[('type_umum', '=', 'jabatan')])
    no_identitas = fields.Char(string='No Identitas')
    npwp = fields.Char(string='NPWP')
    divisi = fields.Char(string='Divisi')
    status_karyawan = fields.Char(string='Status Karyawan')
    jangka_waktu_kontrak = fields.Char(string='Jangka Waktu Kontrak')
    akhir_kontrak = fields.Char(string='Akhir Kontrak')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('done', 'Active'),
        ('close', 'Closed'),
        ('cancel', 'Cancelled'),
        ], string='Status', copy=False, index=True, default='draft', readonly=True)
    email = fields.Char(string='Email', required=True)
    nomor_induk = fields.Char(string='NIK')
    no_telp = fields.Char(string='Telepon')
    no_hp = fields.Char(string='Handphone')
    keluarga_dekat = fields.Char(string='Keluarga Dekat')
    no_keluarga = fields.Char(string='Handphone')
    bank_id = fields.Many2one('res.bank','Bank',help='Nama Bank Penerima')
    bank_norek = fields.Char('Account #',help='No Rekening Penerima')
    bank_namarek = fields.Char('Beneficiary',help='Nama Pada Rekening')
    waris_lines = fields.One2many('simpin.member.waris','member_id',string='Ahli Waris')
    
    ########## DOCUMENT PENDUKUNG ###########
    upload_ktp = fields.Binary(string="KTP")
    file_ktp = fields.Char(string="File KTP")
    upload_ktp_pasangan = fields.Binary(string="KTP Pasangan")
    file_ktp_pasangan = fields.Char(string="File KTP Pasangan")
    upload_kk = fields.Binary(string="Kartu Keluarga")
    file_kk = fields.Char(string="File KK")
    upload_dok_lain = fields.Binary(string="Dokumen Lainnya")
    file_dok_lain = fields.Char(string="File Dokumen Lain")

    _sql_constraints = [
        ('email_uniq', 'unique(email)', 'email must be unique!'),
    ]


    @api.onchange('email')
    def validate_mail(self):
        if self.email:
            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.email)
            if match == None:
                raise ValidationError(_('Not a valid E-mail ID %s')%(self.email,))

 
    def action_submit(self):
#        self.validate_mail()
        self.write({'state': 'submit'})

    def action_check(self):
#        self.validate_mail()
        self.write({'state': 'check'})

    def action_update_data(self):
        member = self.env['simpin.member'].search([('state','=','draft')])
        line_count = 0
        for rec in member:
            partner_id = self.env['res.partner'].create({
                            'name': rec.name,
                            'display_name': rec.name,
                            'active': True,
                            'type': 'contact',
                            'country_id': 100,
                            'is_company': False,
                            'partner_share': True,
                            'company_type':'person',
                            })
            rec.update({'partner_id':partner_id.id,'state': 'done'})
            line_count +=1
            if line_count>1000:
                break


    @api.onchange('provinsi_id')
    def _onchange_provinsi_id(self):
        if self.provinsi_id:
            kabkota = self.env['wilayah.kabkota'].search([('provinsi_id', '=', self.provinsi_id.id)])
            return {'domain': {'kabkota_id': [('id', 'in', kabkota.ids)]}}

    @api.onchange('kabkota_id')
    def _onchange_kabkota_id(self):
        if self.kabkota_id:
            kecamatan = self.env['wilayah.kecamatan'].search([('kabkota_id', '=', self.kabkota_id.id)])
            return {'domain': {'kecamatan_id': [('id', 'in', kecamatan.ids)]}}

    @api.onchange('kecamatan_id')
    def _onchange_kecamatan_id(self):
        if self.kecamatan_id:
            kelurahan = self.env['wilayah.kelurahan'].search([('kecamatan_id', '=', self.kecamatan_id.id)])
            return {'domain': {'kelurahan_id': [('id', 'in', kelurahan.ids)]}}

    @api.onchange('kelurahan_id')
    def _onchange_kelurahan_id(self):
        if self.kelurahan_id:
            self.kodepos = self.kelurahan_id.kodepos


class SimPinMemberWaris(models.Model):
    _name = "simpin.member.waris"
    _description = "Ahli Waris Keanggotaan Simpin"
    _inherit = ['mail.thread']


    name = fields.Char(string='Name', required=True, copy=False, index=True)
    type_identitas = fields.Many2one('master.general', string='Type Identitas', copy=False,
                                     domain=[('type_umum', '=', 'identitas')])
    agama = fields.Many2one('master.general', string='Agama', copy=False,
                                     domain=[('type_umum', '=', 'agama')])
    gender = fields.Many2one('master.general', string='Jenis Kelamin', copy=False,  
                                     domain=[('type_umum', '=', 'gender')])
    hubungan = fields.Many2one('master.general', string='Hubungan', copy=False, required=True,
                                     domain=[('type_umum', '=', 'ahliwaris')])
    hub_lain = fields.Char(string='Lainnya')
    member_id = fields.Many2one('simpin.member',string='Nomor Keanggotaan')
    address = fields.Char(string='Alamat')
    rukun_tetangga = fields.Char(string='RT')
    rukun_warga = fields.Char(string='RW')
    kelurahan_id = fields.Many2one('wilayah.kelurahan',string='Kelurahan')
    kecamatan_id = fields.Many2one('wilayah.kecamatan',string='Kecamatan')
    kabkota_id = fields.Many2one('wilayah.kabkota',string='Kab / Kota')
    provinsi_id = fields.Many2one('wilayah.provinsi',string='Provinsi')
    kodepos =  fields.Char(string='Kodepos',store=True)
    tempat_lahir = fields.Char(string='Tempat Lahir')
    tanggal_lahir = fields.Date(string='Tanggal Lahir')
    no_identitas = fields.Char(string='No Identitas')
    no_telp = fields.Char(string='Telepon')
    no_hp = fields.Char(string='Handphone')

    @api.onchange('provinsi_id')
    def _onchange_provinsi_id(self):
        if self.provinsi_id:
            kabkota = self.env['wilayah.kabkota'].search([('provinsi_id', '=', self.provinsi_id.id)])
            return {'domain': {'kabkota_id': [('id', 'in', kabkota.ids)]}}

    @api.onchange('kabkota_id')
    def _onchange_kabkota_id(self):
        if self.kabkota_id:
            kecamatan = self.env['wilayah.kecamatan'].search([('kabkota_id', '=', self.kabkota_id.id)])
            return {'domain': {'kecamatan_id': [('id', 'in', kecamatan.ids)]}}

    @api.onchange('kecamatan_id')
    def _onchange_kecamatan_id(self):
        if self.kecamatan_id:
            kelurahan = self.env['wilayah.kelurahan'].search([('kecamatan_id', '=', self.kecamatan_id.id)])
            return {'domain': {'kelurahan_id': [('id', 'in', kelurahan.ids)]}}

    @api.onchange('kelurahan_id')
    def _onchange_kelurahan_id(self):
        if self.kelurahan_id:
            self.kodepos = self.kelurahan_id.kodepos

    
