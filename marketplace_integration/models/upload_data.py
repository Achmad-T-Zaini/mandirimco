# -*- coding: utf-8 -*-

import tempfile
import binascii

from datetime import datetime, timedelta, date
import xlrd
from odoo.exceptions import Warning, UserError, AccessError, ValidationError
from odoo import models, fields, exceptions, api,_
import logging
import json
import requests


_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')

class UploadDataMarketPlace(models.TransientModel):
    _name = 'wizard.upload.data'
    _description = "Upload Data MarketPlace"


    file_data = fields.Binary('File', required=True,)
    file_name = fields.Char('File Name')
    marketplaces = fields.Many2one('marketplace.overview', string='MarketPlace', required=True)
    type_data = fields.Selection([
            ('order','Order / Transaksi'),
            ('saldo','Saldo / Balance'),
        ], string='Type Data', default='order', index=True, required=True)

    def upload_batch_data(self):
        if not self.file_data:
            raise Warning('Tidak Ada File Untuk Di Upload')
        fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file_data))
        fp.seek(0)

        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        res = False

        if self.marketplaces.template_data=='tokopedia' and self.type_data=='order':
            res = self.get_tokopedia_order(sheet)
        elif self.marketplaces.template_data=='tokopedia' and self.type_data=='saldo':
            res = self.get_tokopedia_deposit(sheet)
        else:
            raise UserError('Not Defined yet')

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            }

    def _get_product(self,kode_sku,name):
        product_id = self.env['product.product'].search(['|',('name','=',name),('barcode','=',kode_sku)],limit=1)

        return product_id

    def get_tokopedia_order(self,sheet):
        err_list = []
        order_vals = False
        order_line_vals = []
        cont = jml_data = 0
        nama = False
        for row_no in range(sheet.nrows):
            cont += 1
            if row_no <= 4:
                fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                # ====== READ XLS ROW by ROW ========
                no_invoice = line[1]
                if nama!=no_invoice:
                    #Tokopedia Order
                    if nama:
#                        raise UserError(_('order %s')%(order_vals,))
                        toped_id = self.env['tokopedia.order'].search([('name','=',nama)])
                        if toped_id and toped_id.status_order!=line[3]:
                            toped_id.update(order_vals)
                        else:
                            toped_id = self.env['tokopedia.order'].create(order_vals)
                            toped_id.update({'tokopedia_line': order_line_vals,})
                        balance = self.env['tokopedia.deposit'].search([('name','like',nama)])
                        for line in balance:
                            line.update({'tokopedia_id': toped_id.id})
                        
                        order_line_vals = []

                    nama = no_invoice
                    prod_id = self._get_product(line[9],line[8])

                    order_line_vals.append((0,0,{
                        'name': nama,
                        'nama_produk': line[8],
                        'kode_sku': line[9],
                        'catatan_pembeli': line[10],
                        'catatan_penjual': line[11],
                        'product_qty': float(line[12]) if len(line[12])>0 else 0.0,
                        'harga_awal': float(line[13]) if len(line[13])>0 else 0.0,
                        'harga_setelah_diskon': float(line[14]) if len(line[14])>0 else 0.0,
                        'harga_jual': float(line[15]) if len(line[15])>0 else 0.0,
                        'subsidi_tokopedia': float(line[16]) if len(line[16])>0 else 0.0,
                        'voucher_toko_terpakai': float(line[17]) if len(line[17])>0 else 0.0,
                        'jenis_voucher': line[18],
                        'kode_voucher': line[19],
                        'product_id': prod_id.id if prod_id else False,
                    })) 

                    tgl_selesai = tgl_batal = tgl_kirim = False
                    if line[4]:
                        tgl_selesai = datetime.strptime(line[4] + ' ' + line[5],'%d-%m-%Y %H:%M:%S')

                    if line[6]:
                        tgl_batal = datetime.strptime(line[6] + ' ' + line[7],'%d-%m-%Y %H:%M:%S')

                    if line[34]:
                        tgl_kirim = datetime.strptime(line[34] + ' ' + line[35],'%d-%m-%Y %H:%M:%S')

                    if line[20]=='Non Tunai':
                        biaya_kirim = 0.0
                    else:
                        biaya_kirim = float(line[20])

                    order_vals = {
                        'name': nama,
                        'tanggal_pembayaran': datetime.strptime(line[2],'%d-%m-%Y %H:%M:%S'),
                        'status_order': line[3],
                        'tanggal_selesai': tgl_selesai,
                        'tanggal_batal': tgl_batal,
                        'tanggal_kirim': tgl_kirim,
                        'biaya_kirim': biaya_kirim,
                        'biaya_asuransi': float(line[21]) if len(line[21])>0 else 0.0,
                        'total_biaya_kirim': float(line[22]) if len(line[22])>0 else 0.0,
                        'total_penjualan': float(line[23]) if len(line[23])>0 else 0.0,
                        'nama_pembeli': line[24],
                        'telp_pembeli': line[25],
                        'nama_penerima': line[26],
                        'telp_penerima': line[27],
                        'alamat_penerima': line[28],
                        'kota_penerima': line[29],
                        'prov_penerima': line[30],
                        'nama_kurir': line[31],
                        'type_kurir': line[32],
                        'resi_kurir': line[33],
                        'nama_campaign': line[36],
                        'cod': line[37],
                        'mp_id': self.marketplaces.id,
                    } 

                else:
                    #Tokopedia Order Line
                    order_line_vals.append((0,0,{
                        'name': nama,
                        'nama_produk': line[8],
                        'kode_sku': line[9],
                        'catatan_pembeli': line[10],
                        'catatan_penjual': line[11],
                        'product_qty': line[12],
                        'harga_awal': line[13],
                        'harga_setelah_diskon': line[14],
                        'harga_jual': line[15],
                        'subsidi_tokopedia': line[16],
                        'voucher_toko_terpakai': line[17],
                        'jenis_voucher': line[18],
                        'kode_voucher': line[19],
                    })) 
                jml_data += 1

        return

    def get_tokopedia_deposit(self,sheet):
        order_vals = False
        cont = jml_data = 0
        last_balance = self.env['tokopedia.deposit'].search([('tanggal','!=',False)], order='id desc', limit=1)
        if last_balance:
            max_date = last_balance.tanggal
        else:
            max_date = datetime.strptime('2022-01-01 00:00:00','%Y-%m-%d %H:%M:%S')


        for row_no in range(sheet.nrows):
            cont += 1
            if row_no <= 6:
                fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                # ====== READ XLS ROW by ROW ========
                tanggal = datetime.strptime(line[0],'%Y-%m-%d %H:%M:%S')
                if tanggal>max_date:
                    inv_loc = line[1].find('INV/')
                    invoice = False
                    if line[1].find('Pemotongan')>=0:
                        nominal = -float(line[2])
                    else:
                        nominal = float(line[2])


                    toped = False
                    if inv_loc>5:
                        invoice = line[1][inv_loc:]
                        toped_id = self.env['tokopedia.order'].search([('name','=',invoice)])
                        if toped_id:
                            toped = toped_id.id

                    order_vals = {
                        'tanggal': tanggal,
                        'name': line[1],
                        'nominal': nominal,
                        'balance': float(line[3]),
                        'tokopedia_id': toped,
                    } 

#                raise UserError(_('deposit %s\n%s')%(order_vals,invoice,))

                    deposit_id = self.env['tokopedia.deposit'].search([('tanggal','=',tanggal),('name','=',line[1])])
                    if deposit_id:
                        deposit_id.update(order_vals)
                    else:
                        deposit_id = self.env['tokopedia.deposit'].create(order_vals)

                    jml_data += 1

        #Relasikan Saldo dengan Order
        order = self.env['tokopedia.order'].search([('status_order','=','Pesanan Selesai')])
        for rec in order:
            balance = self.env['tokopedia.deposit'].search([('name','like',rec.name)])
            for line in balance:
                line.update({'tokopedia_id': rec.id})

        return

    def get_rajaongkir(self):
        url = "https://api.rajaongkir.com/starter/city"

        payload={"province_id": 12, "Key": "75650a35280cdf8aaf66d3c58a3bab61"}
        headers = {
          'Key': '75650a35280cdf8aaf66d3c58a3bab61',
          'Content-Type': 'application/json'
        }

        response = json.loads(requests.request("GET", url, headers=headers, data=payload).text)

        res = response['rajaongkir']['results']
        for line in res:
            kota = self.env['rajaongkir.kota'].search([('name','=', line['city_name']),('kodepos','=',line['postal_code'])], limit=1)
            if kota:
                kota.update({   'name': line['city_name'],
                                'prov_id': int(line['province_id']),
                                'type_kota': line['type'],
                                'kodepos': line['postal_code'],
                                })
            else:
                prov = self.env['rajaongkir.kota'].create({ 'name': line['city_name'],
                                                            'prov_id': int(line['province_id']),
                                                            'type_kota': line['type'],
                                                            'kodepos': line['postal_code'],
                                                            })
#        raise UserError(_('response %s')%(res,))
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            }


class RajaOngkirProvinsi(models.Model):
    _name = "rajaongkir.provinsi"
    _description = "RajaOngkir Provinsi"

    name = fields.Char(string='Provinsi', copy=False, store=True)

class RajaOngkirKota(models.Model):
    _name = "rajaongkir.kota"
    _description = "RajaOngkir Kab/Kota"

    name = fields.Char(string='Kab / Kota', copy=False, store=True)
    prov_id = fields.Many2one('rajaongkir.provinsi', string='Provinsi', copy=False)
    type_kota = fields.Char(string='Type', copy=False, store=True)
    kodepos = fields.Char(string='Kodepos', copy=False, store=True)