# -*- coding: utf-8 -*-
# Part of Akun+. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from itertools import groupby


class SimPinPinjaman(models.Model):
    _name = "simpin.pinjaman"
    _description = "Pinjaman Anggota Simpin"
    _inherit = ['mail.thread']


    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string='Nomor Pinjaman',default='/')
    member_id = fields.Many2one('simpin.member',string='Nama Anggota', required=True,
                                 domain=[('state', '=', 'done')])
    product_id = fields.Many2one('product.product',string='Product', required=True,
                              readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                                 domain=[('is_simpin', '=', True),('jenis_simpin', '=', 'pinjaman')])
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True, default=_default_currency)
    balance = fields.Monetary(string='Balance',  store=True, currency_field='currency_id', compute='_compute_balance')
    tunggakan = fields.Monetary(string='Tunggakan', currency_field='currency_id', compute='_compute_balance',store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('check', 'Check Document'),
        ('approve', 'Approved'),
        ('active', 'Active'),
        ('close', 'Closed'),
        ('block', 'Blocked'),
        ], string='Status', copy=False, index=True, default='draft', readonly=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    periode_angsuran = fields.Integer(string='Periode Angsuran', required=True, readonly=True,
                                      states={'draft': [('readonly', False)]}, default=6)
    angsuran = fields.Monetary(string='Angsuran',compute='_compute_angsuran',store=True)
    invoice_lines = fields.One2many('account.move', 'pinjaman_id', string='Angsuran', copy=False, domain="[('move_type', '=', 'out_invoice')]")
    tanggal_akad = fields.Date(string='Tanggal Akad', states={'approve': [('readonly', True)]}, index=True, copy=False )
    nilai_pinjaman = fields.Monetary(string='Nilai Pinjaman',currency_field='currency_id',
                                     default=5000000,required=True, copy=False )
    interest = fields.Float(string='interest (%)', required=True, copy=False, default=5)
    payment_id = fields.Many2one('account.payment', string='Pencairan', copy=False )
    journal_id = fields.Many2one('account.journal', string='Journal', copy=False )
    biaya_lines = fields.One2many('pinjaman.biaya', 'pinjaman_id',  string='Komponen Biaya', copy=False )
    jumlah_biaya = fields.Monetary(string='Total Biaya', currency_field='currency_id', copy=False )
    move_pencairan = fields.Many2one('account.move',readonly=True, store=True, string='Journal Pencairan', copy=False )
    notes = fields.Text(string='Keterangan', copy=False )
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company.id)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    ########## DOCUMENT PENDUKUNG ###########
    upload_ktp = fields.Binary(string="Upload KTP")
    file_ktp = fields.Char(string="File KTP")
    upload_ktp_pasangan = fields.Binary(string="Upload KTP Pasangan")
    file_ktp_pasangan = fields.Char(string="File KTP Pasangan")
    upload_kk = fields.Binary(string="Upload KK")
    file_kk = fields.Char(string="File KK")
    upload_npwp = fields.Binary(string="Upload NPWP")
    file_npwp = fields.Char(string="File NPWP")
    upload_slip1 = fields.Binary(string="Upload Slip Gaji #1")
    file_slip1 = fields.Char(string="File Slip Gaji #1")
    upload_slip2 = fields.Binary(string="Upload Slip Gaji #2")
    file_slip2 = fields.Char(string="File Slip Gaji #2")
    upload_slip3 = fields.Binary(string="Upload Slip Gaji #3")
    file_slip3 = fields.Char(string="File Slip Gaji #3")
    upload_dok_lain = fields.Binary(string="Upload Buku Tabungan")
    file_dok_lain = fields.Char(string="File Buku Tabungan")
    
    def get_data_angsuran(self):
        periode = self.periode_angsuran
        angsuran = self.angsuran
        if self.tanggal_akad:
            bulan = self.tanggal_akad
        else:
            bulan = date.today()
            
        pokok_pinjaman = self.nilai_pinjaman
        angsuran_margin = pokok_pinjaman * (self.interest/1200)
        angsuran_pokok = angsuran - angsuran_margin

        result = []
        for i in range(1,periode+1):
            isi_data ={}
            bulan += relativedelta(months=1)
            if i>1:
                pokok_pinjaman -= angsuran_pokok
                angsuran_margin = pokok_pinjaman * (self.interest/1200)
                angsuran_pokok = angsuran - angsuran_margin

            isi_data['no'] = i
            isi_data['periode'] = datetime.strftime(bulan,'%B %Y')
            isi_data['pokok_pinjaman'] = round(pokok_pinjaman,0)
            isi_data['angsuran_pokok'] = round(angsuran_pokok,0)
            isi_data['angsuran_margin'] = round(angsuran_margin,0)
            isi_data['angsuran_bulanan'] = round(angsuran,0)
        
            result.append(isi_data)
        return result  

    @api.onchange('product_id','nilai_pinjaman')
    def _onchange_product_id(self):
        if self.product_id:
            self.update({'biaya_lines': False,})
            biaya_lines = []
            for biaya in self.product_id.biaya_lines:
                subtotal = 0.0
                if biaya.nilai_pct>0:
                    subtotal = round(self.nilai_pinjaman * (biaya.nilai_pct/100),0)
                elif biaya.nominal>0:
                    subtotal = biaya.nominal

                biaya_lines += [(0,0,{'name': biaya.name,
                                      'pinjaman_id': self.id,
                                      'product_id': biaya.product_id.id,
                                      'nilai_pct': biaya.nilai_pct,
                                      'nominal': biaya.nominal,
                                      'is_edit': biaya.is_edit,
                                      'subtotal': subtotal,
                                      })]
            self.update({'biaya_lines': biaya_lines,})


    @api.onchange('biaya_lines','biaya_lines.subtotal')
    def _onchange_biaya_lines(self):
        total = 0
        for line in self.biaya_lines:
            total += line.subtotal
        self.jumlah_biaya = total
        self._compute_angsuran()


    @api.depends('periode_angsuran','nilai_pinjaman','product_id','jumlah_biaya','interest')
    def _compute_angsuran(self):
        margin = periode_max = nilai_max = nilai_min = periode_min = False
        
        if self.product_id and (self.state!='active' or self.state!='close'):
            for line in self.product_id.interest_lines:
                if not periode_max or line.periode_max>periode_max: 
                    periode_max = line.periode_max
                if not periode_min or line.periode_max<periode_min:
                    periode_min = line.periode_min

                if line.periode_max>=self.periode_angsuran:
                    nilai_max = line.nilai_max
                    nilai_min = line.nilai_min
                    margin = line.margin
                    break


            if nilai_min and self.nilai_pinjaman<nilai_min and self.state!='draft':
                self.nilai_pinjaman=nilai_min
                raise UserError(_('Nilai Pinjaman Minimal %s')%('{:,}'.format(nilai_min),))
            elif nilai_max and self.nilai_pinjaman>nilai_max:
                self.nilai_pinjaman=nilai_max
                raise UserError(_('Nilai Pinjaman melebihi Nilai Maksimal %s')%('{:,}'.format(nilai_max),))

            if self.periode_angsuran > periode_max:
                self.periode_angsuran = periode_max
                raise UserError(_('Periode melebihi maksimal %s bulan')%(periode_max,))
            elif self.periode_angsuran < periode_min and self.state!='draft':
                self.periode_angsuran = periode_min
                raise UserError(_('Periode minimal %s bulan')%(periode_min,))

#            raise UserError(_('CP nilai min %s \n nilai max %s \n periode min %s \n periode max %s')%(nilai_min, nilai_max, periode_min,periode_max,))

        currency = self.currency_id or None
        total = self.nilai_pinjaman

        if margin and self.periode_angsuran>0 and total>0:
            angsuran = self.calc_pmt(margin,self.periode_angsuran,total)           
            self.interest = margin
            self.angsuran = round(angsuran,0)

    def calc_pmt(self,margin,periode_angsuran,nilai_pinjaman):
        annual_rate = margin/100
        interest_rate = annual_rate / 12
        present_value = nilai_pinjaman * interest_rate

        angsuran = present_value / (1-((1 + interest_rate)**-periode_angsuran))
        return angsuran


    def action_blokir(self):
        raise UserError('Sub Modul Blokir Pinjaman')

    def action_pelunasan(self):
        raise UserError('Sub Modul Blokir Pelunasan')
        self.update({'state': 'close'})


    def action_approve(self):
        akad_id = "pinjaman sequence"
        rekno = self.env['ir.sequence'].next_by_code(akad_id)
        if not rekno:
            cr_seq = self.env['ir.sequence'].create({
                            'name': 'Pinjaman Sequence',
                            'code': 'pinjaman sequence',
                            'implementation': 'standard',
                            'active': True,
                            'prefix': 'SP-P/%(year)s/%(month)s/',
                            'padding': 5,
                            'company_id': self.env.user.company_id.id,
                            'use_date_range': False,
                            })
            if cr_seq:
                rekno = self.env['ir.sequence'].next_by_code(akad_id)
            else:
                raise UserError('Sequence Error')

        self.name = rekno
        invoice = self.action_create_invoice('in_invoice')
#        raise UserError(_('invoice %s')%(invoice,))
        self.write({'state': 'active',
                    'tanggal_akad': date.today(),
                    'move_pencairan': invoice.id,
#                    'payment_id': payment.id,
                    'balance': self.angsuran * self.periode_angsuran,
                    'name': rekno,})


    def action_submit(self):
        self.write({'state': 'submit'})

    def action_check(self):
        self.write({'state': 'check'})

    def action_create_invoice(self,inv_type):
        """Create Vendor Bill Pencairan.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        for order in self:
            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            if inv_type=='in_invoice':
                invoice_vals = order._prepare_invoice('in_invoice')
                # Invoice line values (keep only necessary sections).
                invoice_vals['invoice_line_ids'].append((0, 0, order._prepare_account_move_line('Piutang Pokok ' + order.name,order.product_id,order.nilai_pinjaman)))
                invoice_vals['invoice_line_ids'].append((0, 0, order._prepare_account_move_line('Piutang Interest ' + order.name,order.product_id,(order.angsuran * order.periode_angsuran)-order.nilai_pinjaman)))
                invoice_vals['invoice_line_ids'].append((0, 0, order._prepare_account_move_line('Piutang Cadangan ' + order.name,order.product_id,-(order.angsuran * order.periode_angsuran)+order.nilai_pinjaman)))
                for biaya in order.biaya_lines:
                    invoice_vals['invoice_line_ids'].append((0, 0, order._prepare_account_move_line(biaya.name,biaya.product_id,-biaya.subtotal)))

                invoice_vals_list.append(invoice_vals)
            elif inv_type=='out_invoice':
                invoice_vals = order._prepare_invoice('out_invoice')
                periode = relativedelta(invoice_vals['invoice_date'],self.tanggal_akad).months - 1
#                raise UserError(_('inv date %s - %s')%(invoice_vals['invoice_date'],periode,))
                data_angsuran = order.get_data_angsuran()[periode]
                invoice_vals['invoice_line_ids'].append((0, 0, order._prepare_account_move_line('Angsuran Pokok ' + order.name,order.product_id,data_angsuran['angsuran_pokok'])))
                invoice_vals['invoice_line_ids'].append((0, 0, order._prepare_account_move_line('Angsuran Margin ' + order.name,order.product_id,data_angsuran['angsuran_margin'])))
                invoice_vals_list.append(invoice_vals)
#                raise UserError(_('vals %s \n %s')%(invoice_vals,invoice_vals_list,))

        if not invoice_vals_list:
            raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list
#        raise UserError(_('vals %s \n %s')%(invoice_vals,invoice_vals_list,))

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type=inv_type)
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()
        cek_aml = []
        for line in moves.line_ids:
            if inv_type=='in_invoice':
                if line.account_id==self.product_id.property_account_expense_id and line.debit==self.nilai_pinjaman:
                    line.update({'account_id': self.product_id.coa_piutang.id, 'account_root_id': self.product_id.coa_piutang.root_id.id,})
                elif line.account_id==self.product_id.property_account_expense_id and line.debit<self.nilai_pinjaman and line.credit==0:
                    line.update({'account_id': self.product_id.coa_piutang_margin.id, 'account_root_id': self.product_id.coa_piutang_margin.root_id.id,})
            elif inv_type=='out_invoice':
                if line.account_id==self.product_id.property_account_expense_id and line.credit==data_angsuran['angsuran_pokok']:
                    line.update({'account_id': self.product_id.coa_piutang.id, 'account_root_id': self.product_id.coa_piutang.root_id.id,})
                elif line.account_id==self.product_id.property_account_expense_id and line.credit==data_angsuran['angsuran_margin']:
                    line.update({'account_id': self.product_id.coa_piutang_margin.id, 'account_root_id': self.product_id.coa_piutang_margin.root_id.id,})

            cek_aml.append({'COA': line.account_id.id,
                            'root': line.account_id.root_id.id,
                            'name': line.name,
                            'account': line.account_id.name,
                            'debit': line.debit,
                            'credit': line.credit,
                            })
#        raise UserError(_('aml %s')%(cek_aml,))
        moves.action_post()
        return moves

    def _prepare_invoice(self,inv_type):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', inv_type)
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        if inv_type=='in_invoice':
            naration = 'Pencairan ' + self.name
            tanggal_inv = date.today()
            pinjaman_id = False
        else:
            pinjaman_id = self.id
            if len(self.invoice_lines)>0:
                last_inv = self.env['account.move'].search([('move_type','=','out_invoice'),('pinjaman_id','=',self.id)],order='id desc',limit=1)
                bulan_inv = relativedelta(last_inv.invoice_date,self.tanggal_akad)
            else:
                last_inv = False
                bulan_inv = relativedelta(date.today(),self.tanggal_akad)

            if last_inv or bulan_inv.days>5:
                bulan = bulan_inv.months + 1
            else:
                bulan = bulan_inv.months

            tanggal_inv = self.tanggal_akad + relativedelta(months=bulan)
#            raise UserError(_('bln %s - %s')%(tanggal_inv,bulan))
            naration = 'Tagihan ' + self.name

        partner_invoice_id = self.member_id.partner_id.address_get(['invoice'])['invoice']
        invoice_vals = {
            'ref': self.name,
            'move_type': move_type,
            'narration': naration,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.env.user.id,
            'partner_id': partner_invoice_id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            'payment_reference': self.name,
            'partner_bank_id': self.member_id.partner_id.bank_ids[:1].id,
            'invoice_origin': self.name,
#            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'invoice_date': tanggal_inv,
            'pinjaman_id': pinjaman_id,
        }
        return invoice_vals

    def action_view_invoice(self, invoices=False):
        """This function returns an action that display existing vendor bills of
        given purchase order ids. When only one found, show the vendor bill
        immediately.
        """
        if not invoices:
            # Invoice_ids may be filtered depending on the user. To ensure we get all
            # invoices related to the purchase order, we read them in sudo to fill the
            # cache.
            self.sudo()._read(['invoice_ids'])
            invoices = self.invoice_ids

        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = invoices.id
        else:
            result = {'type': 'ir.actions.act_window_close'}

        return result

    def _prepare_account_move_line(self,name,product,price):
        self.ensure_one()
        aml_currency = self.currency_id
        date = fields.Date.today()
        res = {
#            'display_type': self.display_type,
            'sequence': 10,
            'name': name,
            'product_id': product.id,
#            'product_uom_id': self.product_uom.id,
            'quantity': 1,
            'price_unit': self.currency_id._convert(price, aml_currency, self.company_id, date, round=False),
#            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'analytic_account_id': self.account_analytic_id.id,
#            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
#            'pinjaman_id': self.id,
        }
        return res

    def create_invoice_pinjaman_daily(self):
        date_today = date.today() #datetime.strptime('2022-01-25','%Y-%m-%d').date() #
        pinjaman = self.env['simpin.pinjaman'].search([('state','=','active')])
        counter = 0
        for rec in pinjaman:
            invoice = False
            if len(rec.invoice_lines)>0:
                last_inv = self.env['account.move'].search([('move_type','=','out_invoice'),('pinjaman_id','=',self.id)],order='id desc',limit=1)
                bulan_inv = relativedelta(date.today(),last_inv.invoice_date)
            else:
                last_inv = False
                bulan_inv = relativedelta(date.today(),self.tanggal_akad)

#            raise UserError(_('bln_inv %s - %s')%(last_inv,bulan_inv))
            if bulan_inv.months>=1:
                invoice = rec.action_create_invoice('out_invoice')
            if invoice:
#                rec.update({'invoice_lines': [(0,0,invoice.id)]})
                balance = rec.angsuran * rec.periode_angsuran
                tunggakan = 0
                for inv in rec.invoice_lines:
                    if inv.payment_state=='paid':
                        balance -= rec.angsuran
                    else:
                        tunggakan +=rec.angsuran
                rec.write({
                            'balance': balance,
                            'tunggakan': tunggakan,
                            })
#                raise UserError(_('rec %s - %s')%(rec.balance,rec.tunggakan))

class AccountMove(models.Model):
    _inherit = "account.move"

    pinjaman_id = fields.Many2one('simpin.pinjaman',string='Pinjaman')
    investasi_id = fields.Many2one('simpin.investasi',string='Investasi')


class AccountPayment(models.Model):
    _inherit = "account.payment"

    pinjaman_id = fields.Many2one('simpin.pinjaman',string='Pinjaman')
    investasi_id = fields.Many2one('simpin.investasi',string='Investasi')
    margin_amount = fields.Float(string='Margin Amount',default=0.0, copy=False)


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    pinjaman_id = fields.Many2one('simpin.pinjaman',string='Pinjaman')
    investasi_id = fields.Many2one('simpin.investasi',string='Investasi')

    def _create_payments(self):
        self.ensure_one()
        batches = self._get_batches()
        edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)

        to_reconcile = []
        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard()
            payment_vals_list = [payment_vals]
            to_reconcile.append(batches[0]['lines'])
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'lines': line,
                        })
                batches = new_batches

            payment_vals_list = []
            for batch_result in batches:
                payment_vals_list.append(self._create_payment_vals_from_batch(batch_result))
                to_reconcile.append(batch_result['lines'])

#        raise UserError(_('payment_vals_list %s')%(payment_vals_list,))
        payments = self.env['account.payment'].create(payment_vals_list)

        # If payments are made using a currency different than the source one, ensure the balance match exactly in
        # order to fully paid the source journal items.
        # For example, suppose a new currency B having a rate 100:1 regarding the company currency A.
        # If you try to pay 12.15A using 0.12B, the computed balance will be 12.00A for the payment instead of 12.15A.
        if edit_mode:
            for payment, lines in zip(payments, to_reconcile):
                # Batches are made using the same currency so making 'lines.currency_id' is ok.
                if payment.currency_id != lines.currency_id:
                    liquidity_lines, counterpart_lines, writeoff_lines = payment._seek_for_lines()
                    source_balance = abs(sum(lines.mapped('amount_residual')))
                    payment_rate = liquidity_lines[0].amount_currency / liquidity_lines[0].balance
                    source_balance_converted = abs(source_balance) * payment_rate

                    # Translate the balance into the payment currency is order to be able to compare them.
                    # In case in both have the same value (12.15 * 0.01 ~= 0.12 in our example), it means the user
                    # attempt to fully paid the source lines and then, we need to manually fix them to get a perfect
                    # match.
                    payment_balance = abs(sum(counterpart_lines.mapped('balance')))
                    payment_amount_currency = abs(sum(counterpart_lines.mapped('amount_currency')))
                    if not payment.currency_id.is_zero(source_balance_converted - payment_amount_currency):
                        continue

                    delta_balance = source_balance - payment_balance

                    # Balance are already the same.
                    if self.company_currency_id.is_zero(delta_balance):
                        continue

                    # Fix the balance but make sure to peek the liquidity and counterpart lines first.
                    debit_lines = (liquidity_lines + counterpart_lines).filtered('debit')
                    credit_lines = (liquidity_lines + counterpart_lines).filtered('credit')

                    payment.move_id.write({'line_ids': [
                        (1, debit_lines[0].id, {'debit': debit_lines[0].debit + delta_balance}),
                        (1, credit_lines[0].id, {'credit': credit_lines[0].credit + delta_balance}),
                    ]})

        if payments.pinjaman_id or payments.investasi_id:
            for payment in payments:
            # Lanjut cek AML yg sudah terbentuk dan menambahkan aml pendapatan margin
                new_aml = []
                if payment.pinjaman_id:
                    account_analytic_id = payment.pinjaman_id.account_analytic_id
                    coa_cadangan = payment.pinjaman_id.product_id.property_account_expense_id
                    coa_pendapatan = payment.pinjaman_id.product_id.coa_margin
                    new_aml.append(self._prepare_account_move_line(coa_pendapatan,payment.move_id,account_analytic_id,payment.margin_amount,0))
                    new_aml.append(self._prepare_account_move_line(coa_pendapatan,payment.move_id,account_analytic_id,0,payment.margin_amount))
                    aml = self.env['account.move.line'].create(new_aml)
        payments.action_post()

        if payments.pinjaman_id or payments.investasi_id:
            for payment in payments:
            # Lanjut cek AML yg sudah terbentuk dan menambahkan aml pendapatan margin
                cek_aml = []
                if payment.pinjaman_id:
                    coa_cadangan = payment.pinjaman_id.product_id.property_account_expense_id
                    coa_pendapatan = payment.pinjaman_id.product_id.coa_margin

                    for line in payment.move_id.line_ids:
                        if line.account_id==coa_pendapatan and line.debit>0:
                            line.update({'name': coa_cadangan.name})
                            csql = ("update account_move_line set account_id=%s,account_root_id=%s where id=%s")%(coa_cadangan.id,coa_cadangan.root_id.id,line.id)
                            self.env.cr.execute(csql)
#                            line.update({'account_id': coa_cadangan.id, 'account_root_id': coa_cadangan.root_id.id, 'name': coa_cadangan.name})


                for line in payment.move_id.line_ids:
                    cek_aml.append({'COA': line.account_id.id,
                                    'root': line.account_id.root_id.id,
                                    'name': line.name,
                                    'account': line.account_id.name,
                                    'debit': line.debit,
                                    'credit': line.credit,
                                    })

#                raise UserError(_('POSTED pinjaman_id %s\ninvestasi_id %s\naml %s')%(payment.pinjaman_id.name,payment.investasi_id.name,cek_aml,))

        domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
        for payment, lines in zip(payments, to_reconcile):

            # When using the payment tokens, the payment could not be posted at this point (e.g. the transaction failed)
            # and then, we can't perform the reconciliation.
            if payment.state != 'posted':
                continue

            payment_lines = payment.line_ids.filtered_domain(domain)
            for account in payment_lines.account_id:
                (payment_lines + lines)\
                    .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
                    .reconcile()

        return payments
        
    def _prepare_account_move_line(self,account_id,move,account_analytic_id,debit=0,credit=0):
        res = {
            'sequence': 10,
            'move_id': move.id,
            'date': move.date,
            'ref': account_id.name,
            'journal_id': move.journal_id.id,
            'company_id': move.company_id.id,
            'company_currency_id': move.currency_id.id,
            'account_id': account_id.id,
            'account_root_id': account_id.root_id.id,
            'name': account_id.name,
            'quantity': 1,
            'debit': debit,
            'credit': credit,
            'balance': debit - credit,
            'amount_currency': debit - credit,
            'date_maturity': move.date,
            'currency_id': move.currency_id.id,
            'partner_id': move.partner_id.id,
            'analytic_account_id': account_analytic_id.id,
            'payment_id': move.payment_id.id,
            }
        return res


    @api.model
    def _get_line_batch_key(self, line):
        ''' Turn the line passed as parameter to a dictionary defining on which way the lines
        will be grouped together.
        :return: A python dictionary.
        '''
        move = line.move_id

        partner_bank_account = self.env['res.partner.bank']
        if move.is_invoice(include_receipts=True):
            partner_bank_account = move.partner_bank_id._origin

        return {
            'partner_id': line.partner_id.id,
            'account_id': line.account_id.id,
            'currency_id': line.currency_id.id,
            'partner_bank_id': partner_bank_account.id,
            'partner_type': 'customer' if line.account_internal_type == 'receivable' else 'supplier',
            'payment_type': 'inbound' if line.balance > 0.0 else 'outbound',
            'pinjaman_id': move.pinjaman_id.id,
            'investasi_id': move.investasi_id.id,
        }

    def _create_payment_vals_from_batch(self, batch_result):
        batch_values = self._get_wizard_values_from_batch(batch_result)
        margin_amount = 0
        coa_margin=False
        if batch_result['key_values']['pinjaman_id'] or batch_result['key_values']['investasi_id']:
            if batch_result['key_values']['pinjaman_id']:
                pinjaman_id = self.env['simpin.pinjaman'].search([('id','=',batch_result['key_values']['pinjaman_id'])])
                coa_margin = pinjaman_id.product_id.coa_piutang_margin.id
                for line in batch_result['lines'][0].move_id.line_ids:
                    if coa_margin and line.account_id.id==coa_margin:
                        margin_amount = line.credit

        if batch_values['payment_type'] == 'inbound':
            partner_bank_id = self.journal_id.bank_account_id.id
        else:
            partner_bank_id = batch_result['key_values']['partner_bank_id']

        return {
            'date': self.payment_date,
            'amount': batch_values['source_amount_currency'],
            'payment_type': batch_values['payment_type'],
            'partner_type': batch_values['partner_type'],
            'ref': self._get_batch_communication(batch_result),
            'journal_id': self.journal_id.id,
            'currency_id': batch_values['source_currency_id'],
            'partner_id': batch_values['partner_id'],
            'partner_bank_id': partner_bank_id,
            'payment_method_id': self.payment_method_id.id,
            'destination_account_id': batch_result['lines'][0].account_id.id,
            'pinjaman_id': batch_result['key_values']['pinjaman_id'],
            'investasi_id': batch_result['key_values']['investasi_id'],
            'margin_amount': margin_amount,
        }

    def _create_payment_vals_from_wizard(self):
        margin_amount = 0
        coa_margin=False
        if self.line_ids[0].move_id.pinjaman_id or self.line_ids[0].move_id.investasi_id:
            cek_aml = []
            if self.line_ids[0].move_id.pinjaman_id:
                coa_margin = self.line_ids[0].move_id.pinjaman_id.product_id.coa_piutang_margin.id

            for line in self.line_ids[0].move_id.line_ids:
                if coa_margin and line.account_id.id==coa_margin:
                    if self.line_ids[0].move_id.pinjaman_id:
                        margin_amount = line.credit
                    cek_aml.append({'COA': line.account_id.id,
                                    'root': line.account_id.root_id.id,
                                    'name': line.name,
                                    'account': line.account_id.name,
                                    'debit': line.debit,
                                    'credit': line.credit,
                                    })

        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_id': self.payment_method_id.id,
            'destination_account_id': self.line_ids[0].account_id.id,
            'pinjaman_id': self.line_ids[0].move_id.pinjaman_id.id,
            'investasi_id': self.line_ids[0].move_id.investasi_id.id,
            'margin_amount': margin_amount,
        }
        
        if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
            payment_vals['write_off_line_vals'] = {
                'name': self.writeoff_label,
                'amount': self.payment_difference,
                'account_id': self.writeoff_account_id.id,
            }
        return payment_vals

class PinjamanBiaya(models.Model):
    _name = "pinjaman.biaya"
    _description = "Komponen Biaya Pinjaman Anggota Simpin"


    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string='Biaya', related='product_id.name')
    product_id = fields.Many2one('product.product',string='Product', required=True,
                              readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                                 domain=[('type', '=', 'service')])
    pinjaman_id = fields.Many2one('simpin.pinjaman',string='Pinjaman')
    nilai_pct = fields.Float(default=0.0, string='Pct (%)')
    nominal = fields.Float(default=0.0, string='Nominal')
    subtotal = fields.Monetary(string='Sub Total', compute='_compute_harga', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True, default=_default_currency)
    is_edit = fields.Boolean(string='Editable', default=False)

    @api.depends('nilai_pct','nominal')
    def _compute_harga(self):
        for rec in self:
            if rec.nilai_pct!=0:
                rec.subtotal = round(rec.pinjaman_id.nilai_pinjaman * rec.nilai_pct / 100,0)
            elif rec.nominal>0:
                rec.subtotal = rec.nominal
            else:
                rec.subtotal = 0.0
   
