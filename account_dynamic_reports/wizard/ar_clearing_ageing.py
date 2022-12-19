from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT



from odoo import api, fields, models

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    account_ar_id = fields.Many2one(comodel_name='account.account', string='Account AR Clearing',readonly=False)
    account_ap_id = fields.Many2one(comodel_name='account.account', string='Account AP Clearing',readonly=False)



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    account_ar_id = fields.Many2one(comodel_name='account.account', string='Account AR Clearing',related='company_id.account_ar_id',readonly=False)
    account_ap_id = fields.Many2one(comodel_name='account.account', string='Account AP Clearing',related='company_id.account_ap_id',readonly=False)
    



class InsPartnerAgeing(models.TransientModel):
    _inherit = "ins.partner.ageing"
    

    @api.model
    def default_get(self, fields):
        rec = super(InsPartnerAgeing, self).default_get(fields)
        vals = self._context
        clearing = {
            'ar': self.env['res.company']._company_default_get('account.account').account_ar_id,
            'ap': self.env['res.company']._company_default_get('account.account').account_ap_id

        }
        hasil = False
        if vals.get('clearing'):
            hasil = clearing[vals['clearing']]        
            rec['account_ids'] = [hasil.id]
            if not hasil:
                raise ValidationError("Akun AR/AP Clearing tidak ditemuan, setting di Configurations = > Settings = > Account AR/AP Clearing Ageing Reports")

        
        return rec