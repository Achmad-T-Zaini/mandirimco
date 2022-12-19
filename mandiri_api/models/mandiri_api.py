# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError, ValidationError
from datetime import datetime,date
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from base64 import b64encode, b64decode
from dateutil.relativedelta import relativedelta

import requests
import hashlib
import hmac
import json
import os


class MandiriApiConnect(models.Model):
    _name = "mandiri_api.connect"
    _description = "Mandiri API"

    name = fields.Char('API Name')
#    bank_id = fields.Many2one('res.bank',string='Bank')
    privatekey_filedata = fields.Binary(string='Upload PrivateKey File')
    privatekey_filename = fields.Char(string="PrivateKey File")
    privatekey_password = fields.Char(string='PrivateKey Password')
    client_id = fields.Char('Client ID') 
    client_secret = fields.Char(string='Client Secret')
    partner_id = fields.Char('Partner ID') 
    external_id = fields.Char('External ID') 
    no_rek = fields.Char(string='Bank Account')
    url_path = fields.Char(string='url path')
    url_token = fields.Char(string='url Token')
    url_balance = fields.Char(string='url Balance Inquiry')
    url_loan = fields.Char(string='url Loan Inquiry')
    url_trx_saving = fields.Char(string='url Trx Saving')
    url_trx_loan = fields.Char(string='url Trx Loan')
    url_acc_info_internal = fields.Char(string='url Account Info Internal')
    url_acc_info_external = fields.Char(string='url Account Info External')
    url_inhouse_trf = fields.Char(string='url Inhouse Transfer')
    url_rtgs_trf = fields.Char(string='url RTGS Transfer')
    url_skn_trf = fields.Char(string='url SKN Transfer')
    url_interbank = fields.Char(string='url Interbank Transfer')
    url_trf_status = fields.Char(string='url Transfer Status')
    url_bill_inquiry = fields.Char(string='url Bill Payment Inquiry')
    url_bill_payment = fields.Char(string='url Bill Payment')
    
    def load_privatekey(self, privatekey_file, privatekey_password):
        ll=open(privatekey_file).read()
        return RSA.importKey(open(privatekey_file).read(), privatekey_password)

    def generate_signature(self, data, private_key):
        digest = SHA256.new()
        digest.update(str.encode(data))
        signer = PKCS1_v1_5.new(private_key)
        sign = signer.sign(digest)
        return b64encode(sign).decode()

    def get_signature(self, data, privatekey_file, privatekey_password):
        private_key = self.load_privatekey(privatekey_file, privatekey_password)
        signature = self.generate_signature(data, private_key)
        return signature

    def get_token(self,tgl_jam):
        url = self.url_path + self.url_token
#        dt_time = datetime.now() + relativedelta(hours=7)
#        tgl_jam = dt_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3].replace(' ','T') + 'T+0700'
        data = self.client_id + "|" + tgl_jam

        cwd = os.getcwd()
        privatekey_file =  '/opt/odoo14_mco/odoo-custom-addons/mandiri_api/security/' + self.privatekey_filename

        signature = self.get_signature(data, privatekey_file, self.privatekey_password)

        headers = {
          'X-Mandiri-Key': self.client_id,
          'X-TIMESTAMP': tgl_jam,
          'X-SIGNATURE': signature,
          'Content-Type': 'application/x-www-form-urlencoded',
          'Cookie': 'visid_incap_2120482=+cbSgiWiRvayjsTlG+aoeM04w2AAAAAAQUIPAAAAAABVi6LmnAYdmAb0tLf+YDu1; incap_ses_1132_2120482=0cgoG2SD8B/ftxZtW6y1D0PY4mAAAAAAPZD6kuYJbaabQlN6AbiFTw==; nlbi_2120482=nfBydYhGJWFGfBsB2AR7JgAAAACN3JbcjEAayVy9ezhcnwW7'
          }
        payload='grant_type=client_credentials'
        response = requests.request("POST", url, headers=headers, data=payload)
#        raise UserError(_('client_id %s \n timestamp %s \n token %s')%(self.client_id,tgl_jam,response.text,))        
        token =json.loads(response.text) 
        return token['accessToken']

    def get_info(self,url,payload):
        http_method = 'POST'
#        url = self.url_balance
        url_path = self.url_path + url
        dt_time = datetime.now() + relativedelta(hours=7)
        tgl_jam = dt_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3].replace(' ','T') + 'T+0700'

        client_secret = bytes(self.client_secret,'utf-8')
        token = self.get_token(tgl_jam)
        
        to_sign = http_method + ':' + url + ':' + token + ':' + payload + ':' + tgl_jam

#        client_secret = bytes('20a8e607-12fc-4fd1-8dff-c3954a30b81b','utf-8')
#        to_sign = 'POST:/openapi/transactions/v1.0/fundTransfer/inhouse:eyJraWQiOiJzc29zIiwiYWxnIjoiUlM1MTIifQ.eyJzdWIiOiJzeXM6ZGVmYXVsdEFwcGxpY2F0aW9uIiwiYXVkIjpbInN5czpkZWZhdWx0QXBwbGljYXRpb24iLCJqd3QtYXVkIl0sImNsaWVudElkIjoiMzAyZGUwNWMtMGU3OC00MjU2LWJjZTEtMTUwZDg5MTM0MjA4IiwicGFydG5lcnRJZCI6IlVBVENPUlBBWSIsImlzcyI6Imp3dC1pc3N1ZXIiLCJleHAiOjE1OTczMDg2NzYsImlhdCI6MTU5NzMwNzc3Nn0.B4yR0bzauZ7ww-x7p22FTCTg-JlxqGBXmieS-DEqAh9DyRoSnROO-j5hotQWA8MnxfgpQg7tI5dxjoHqLeWKNa_MKD1DrqcpG3Xu1JN-3H3n3DWeyqzdbfzShTMG6WgVXTBSr_9eeb0COQZS3wO9onVwt5Aq8bgNwDb35Q4HHEcRDxGDbRv51Xy-GgEqo-e80_Io3w8V0LCkAZCutcGHtnoo2R5MOFtrWnSMa1_Ca8GPxduFHNzWs-1oGOEGLjfrnAPyNQv4OjPO7zGpiGa_qZJuVDODPM7cxUCYf9sEcx92bR1z8qorVntm9pGVERQTDx1KeDv6GVCszbx9MYoCFA:{"debitAccountNo":"1150006399259","creditAccountNo":"60004398552","creditAmount":"100000","creditCurrency":"IDR","valueDate":"2020-08-13","customerReferenceNo":"123124712331","remark":"123124712331","beneficiaryEmailAddress":"api.support@bankmandiri.co.id"}:2020-08-13T19:44:24.000T+0700'

        sign = hmac.new(client_secret, to_sign.encode('utf8'), hashlib.sha512).hexdigest()
#        raise UserError(_('token %s\nto_sign %s \n %s')%(token,to_sign,sign))

        headers = {
#          'X-Mandiri-Key': self.client_id,
          'Authorization': 'Bearer ' + token,
          'X-TIMESTAMP': tgl_jam,
          'X-SIGNATURE': sign,
          'X-PARTNER-ID': self.partner_id,
          'X-EXTERNAL-ID': self.external_id,
          'Content-Type': 'application/json',
          'Cookie': 'visid_incap_2120482=+cbSgiWiRvayjsTlG+aoeM04w2AAAAAAQUIPAAAAAABVi6LmnAYdmAb0tLf+YDu1; incap_ses_1132_2120482=0cgoG2SD8B/ftxZtW6y1D0PY4mAAAAAAPZD6kuYJbaabQlN6AbiFTw==; nlbi_2120482=nfBydYhGJWFGfBsB2AR7JgAAAACN3JbcjEAayVy9ezhcnwW7'
          }
        
#        raise UserError(_('url_path %s \n headers %s \n payload %s')%(url_path,headers,payload,))
        response = requests.request("POST", url_path, headers=headers, data=payload)

        return response.text



    def info_balance(self):
        payload='{"accountNo":"' + self.no_rek + '"}'
        res = self.get_info(self.url_balance,payload)
        raise UserError(_('response %s')%(res,))
    
    def info_loan(self):
        payload='{"accountNo":"' + self.no_rek + '"}'
        res = self.get_info(self.url_loan,payload)
        raise UserError(_('response %s')%(res,))

    def info_trx_saving(self):
        payload='{"accountNo":"' + self.no_rek + '","postingTime":"13:05:00.0Z"}'
        res = self.get_info(self.url_trx_saving,payload)
        raise UserError(_('response %s')%(res,))

