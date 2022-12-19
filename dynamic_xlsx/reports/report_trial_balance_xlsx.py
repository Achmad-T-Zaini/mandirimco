# _*_ coding: utf-8
from odoo import models, fields, api,_
from odoo.http import content_disposition, request
from odoo.modules.module import get_resource_path
import random as rand

from datetime import datetime
try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
    from xlsxwriter.utility import xl_rowcol_to_cell
except ImportError:
    ReportXlsx = object

DATE_DICT = {
    '%m/%d/%Y' : 'mm/dd/yyyy',
    '%Y/%m/%d' : 'yyyy/mm/dd',
    '%m/%d/%y' : 'mm/dd/yy',
    '%d/%m/%Y' : 'dd/mm/yyyy',
    '%d/%m/%y' : 'dd/mm/yy',
    '%d-%m-%Y' : 'dd-mm-yyyy',
    '%d-%m-%y' : 'dd-mm-yy',
    '%m-%d-%Y' : 'mm-dd-yyyy',
    '%m-%d-%y' : 'mm-dd-yy',
    '%Y-%m-%d' : 'yyyy-mm-dd',
    '%f/%e/%Y' : 'm/d/yyyy',
    '%f/%e/%y' : 'm/d/yy',
    '%e/%f/%Y' : 'd/m/yyyy',
    '%e/%f/%y' : 'd/m/yy',
    '%f-%e-%Y' : 'm-d-yyyy',
    '%f-%e-%y' : 'm-d-yy',
    '%e-%f-%Y' : 'd-m-yyyy',
    '%e-%f-%y' : 'd-m-yy'
}

class InsTrialBalanceXlsx(models.AbstractModel):
    _name = 'report.dynamic_xlsx.ins_trial_balance_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Available formats:
         * format_title
         * format_header
        """
        self.format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'font': 'Arial',
        })
        self.format_title2 = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 24,
            'font': 'Arial',
            'font_color': 'red',
            'valign': 'vcenter',
        })
        self.format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font': 'Arial',
            #'border': True
        })
        self.format_merged_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'right': True,
            'left': True,
            'font': 'Arial',
        })
        self.format_merged_header_without_border = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
        })
        self.content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'font': 'Arial',
        })
        self.line_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
        })
        self.line_header_total = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'top': True,
            'bottom': True,
        })
        self.line_header_left = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
        })
        self.line_header_left_total = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
            'top': True,
            'bottom': True,
        })
        self.line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
        })
        self.line_header_light_total = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'top': True,
            'bottom': True,
        })
        self.line_header_light_left = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
        })
        self.line_header_highlight = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
        })
        self.line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
        })

    def prepare_report_filters(self, data, filter, sheet_2,row_pos_2, language_id, format_header,line_header_light_date, content_header):
        """It is writing under second page"""
        row_pos_2 += 2
        if filter:
            # Date from
            sheet_2.write_string(row_pos_2, 0, _('Date from'),
                                    format_header)
            sheet_2.write_datetime(row_pos_2, 1, self.convert_to_date(language_id,str(filter['date_from']) or ''),
                                    line_header_light_date)
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Date to'),
                                    format_header)
            sheet_2.write_datetime(row_pos_2, 1, self.convert_to_date(language_id,str(filter['date_to']) or ''),
                                    line_header_light_date)

            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Display accounts'),
                                    format_header)
            sheet_2.write_string(row_pos_2, 1, filter['display_accounts'],
                                    content_header)

            # Journals
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Journals'),
                                    format_header)
            j_list = ', '.join([lt or '' for lt in filter.get('journals')])
            sheet_2.write_string(row_pos_2, 1, j_list,
                                      content_header)

            # Accounts
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Analytic Accounts'),
                                      format_header)
            a_list = ', '.join([lt or '' for lt in filter.get('analytics')])
            sheet_2.write_string(row_pos_2, 1, a_list,
                                      content_header)

            # Accounts
            # row_pos_2 += 1
            # sheet_2.write_string(row_pos_2, 0, _('Accounts'),
            #                         self.format_header)
            # a_list = ', '.join([lt or '' for lt in filter.get('accounts')])
            # sheet_2.write_string(row_pos_2, 1, a_list,
            #                           self.content_header)

            # Branches
            # row_pos_2 += 1
            # sheet_2.write_string(row_pos_2, 0, _('Branch'),
            #                           self.format_header)
            # a_list = ', '.join([lt or '' for lt in filter.get('operating_location_ids')])
            # sheet_2.write_string(row_pos_2, 1, a_list,
            #                           self.content_header)

    def prepare_report_contents(self, acc_lines, retained, subtotal, filter, sheet, row_pos, language_id, format_merged_header, format_merged_header_without_border,
            format_header, line_header_light_left, line_header_light, line_header_highlight,line_header_left_total, line_header_light_total, line_header_total):

        row_pos += 5
        sheet.merge_range(row_pos, 1, row_pos, 3, 'Initial Balance', format_merged_header)

        sheet.write_datetime(row_pos, 4, self.convert_to_date(language_id,filter.get('date_from')),
                                  format_merged_header_without_border)
        sheet.write_string(row_pos, 5, _(' To '),
                                  format_merged_header_without_border)
        sheet.write_datetime(row_pos, 6, self.convert_to_date(language_id,filter.get('date_to')),
                                  format_merged_header_without_border,)

        sheet.merge_range(row_pos, 7, row_pos, 9, 'Ending Balance', format_merged_header)

        row_pos += 2

        sheet.write_string(row_pos, 0, _('Account'),
                                format_header)
        sheet.write_string(row_pos, 1, _('Debit'),
                                format_header)
        sheet.write_string(row_pos, 2, _('Credit'),
                                format_header)
        sheet.write_string(row_pos, 3, _('Balance'),
                                format_header)
        sheet.write_string(row_pos, 4, _('Debit'),
                                format_header)
        sheet.write_string(row_pos, 5, _('Credit'),
                                format_header)
        sheet.write_string(row_pos, 6, _('Balance'),
                                format_header)
        sheet.write_string(row_pos, 7, _('Debit'),
                                format_header)
        sheet.write_string(row_pos, 8, _('Credit'),
                                format_header)
        sheet.write_string(row_pos, 9, _('Balance'),
                                format_header)

        if acc_lines:
            if not filter.get('show_hierarchy'):
                for line in acc_lines: # Normal lines
                    row_pos += 1
                    sheet.write_string(row_pos, 0,  acc_lines[line].get('code') + ' ' +acc_lines[line].get('name'), line_header_light_left)
                    sheet.write_number(row_pos, 1, float(acc_lines[line].get('initial_debit')), line_header_light)
                    sheet.write_number(row_pos, 2, float(acc_lines[line].get('initial_credit')), line_header_light)
                    sheet.write_number(row_pos, 3, float(acc_lines[line].get('initial_balance')), line_header_highlight)
                    sheet.write_number(row_pos, 4, float(acc_lines[line].get('debit')), line_header_light)
                    sheet.write_number(row_pos, 5, float(acc_lines[line].get('credit')), line_header_light)
                    sheet.write_number(row_pos, 6, float(acc_lines[line].get('balance')), line_header_highlight)
                    sheet.write_number(row_pos, 7, float(acc_lines[line].get('ending_debit')), line_header_light)
                    sheet.write_number(row_pos, 8, float(acc_lines[line].get('ending_credit')), line_header_light)
                    sheet.write_number(row_pos, 9, float(acc_lines[line].get('ending_balance')), line_header_highlight)
            else:
                for line in acc_lines: # Normal lines
                    row_pos += 1
                    blank_space = '   ' * len(line.get('indent_list'))
                    if line.get('dummy'):
                        sheet.write_string(row_pos, 0,  blank_space + line.get('code'),
                                                line_header_light_left)
                    else:
                        sheet.write_string(row_pos, 0, blank_space + line.get('code') + ' ' + line.get('name'),
                                                line_header_light_left)
                    sheet.write_number(row_pos, 1, float(line.get('initial_debit')), line_header_light)
                    sheet.write_number(row_pos, 2, float(line.get('initial_credit')), line_header_light)
                    sheet.write_number(row_pos, 3, float(line.get('initial_balance')), line_header_highlight)
                    sheet.write_number(row_pos, 4, float(line.get('debit')), line_header_light)
                    sheet.write_number(row_pos, 5, float(line.get('credit')), line_header_light)
                    sheet.write_number(row_pos, 6, float(line.get('balance')), line_header_highlight)
                    sheet.write_number(row_pos, 7, float(line.get('ending_debit')), line_header_light)
                    sheet.write_number(row_pos, 8, float(line.get('ending_credit')), line_header_light)
                    sheet.write_number(row_pos, 9, float(line.get('ending_balance')), line_header_highlight)


            if filter.get('strict_range'):
                # Retained Earnings line
                row_pos += 1
                sheet.write_string(row_pos, 0, '        ' + retained['RETAINED'].get('name'), line_header_light_left)
                sheet.write_number(row_pos, 1, float(retained['RETAINED'].get('initial_debit')), line_header_light)
                sheet.write_number(row_pos, 2, float(retained['RETAINED'].get('initial_credit')), line_header_light)
                sheet.write_number(row_pos, 3, float(retained['RETAINED'].get('initial_balance')), line_header_highlight)
                sheet.write_number(row_pos, 4, float(retained['RETAINED'].get('debit')), line_header_light)
                sheet.write_number(row_pos, 5, float(retained['RETAINED'].get('credit')), line_header_light)
                sheet.write_number(row_pos, 6, float(retained['RETAINED'].get('balance')), line_header_highlight)
                sheet.write_number(row_pos, 7, float(retained['RETAINED'].get('ending_debit')), line_header_light)
                sheet.write_number(row_pos, 8, float(retained['RETAINED'].get('ending_credit')), line_header_light)
                sheet.write_number(row_pos, 9, float(retained['RETAINED'].get('ending_balance')), line_header_highlight)
            # Sub total line
            row_pos += 2
            sheet.write_string(row_pos, 0,  subtotal['SUBTOTAL'].get('code') + ' ' + subtotal['SUBTOTAL'].get('name'), line_header_left_total)
            sheet.write_number(row_pos, 1,float(subtotal['SUBTOTAL'].get('initial_debit')), line_header_light_total)
            sheet.write_number(row_pos, 2, float(subtotal['SUBTOTAL'].get('initial_credit')), line_header_light_total)
            sheet.write_number(row_pos, 3, float(subtotal['SUBTOTAL'].get('initial_balance')), line_header_total)
            sheet.write_number(row_pos, 4, float(subtotal['SUBTOTAL'].get('debit')), line_header_light_total)
            sheet.write_number(row_pos, 5, float(subtotal['SUBTOTAL'].get('credit')), line_header_light_total)
            sheet.write_number(row_pos, 6, float(subtotal['SUBTOTAL'].get('balance')), line_header_total)
            sheet.write_number(row_pos, 7, float(subtotal['SUBTOTAL'].get('ending_debit')), line_header_light_total)
            sheet.write_number(row_pos, 8, float(subtotal['SUBTOTAL'].get('ending_credit')), line_header_light_total)
            sheet.write_number(row_pos, 9, float(subtotal['SUBTOTAL'].get('ending_balance')), line_header_total)

    def _format_float_and_dates(self, currency_id, lang_id,line_header, line_header_light, line_header_highlight,line_header_light_date, format_merged_header_without_border):

        line_header.num_format = currency_id.excel_format

        line_header_light.num_format = currency_id.excel_format

        line_header_highlight.num_format = currency_id.excel_format

        line_header_light_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')
        format_merged_header_without_border.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')

    def convert_to_date(self, language_id, datestring=False):
        if datestring:
            datestring = fields.Date.from_string(datestring).strftime(language_id.date_format)
            return datetime.strptime(datestring, language_id.date_format)
        else:
            return False

    def generate_xlsx_report(self, workbook, data, record):
        format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'font': 'Arial',
        })
        format_title2 = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 24,
            'font': 'Arial',
            'font_color': 'red',
            'valign': 'vcenter',
        })
        format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font': 'Arial',
            #'border': True
        })
        format_merged_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'right': True,
            'left': True,
            'font': 'Arial',
        })
        format_merged_header_without_border = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
        })
        content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'font': 'Arial',
        })
        line_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
        })
        line_header_total = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'top': True,
            'bottom': True,
        })
        line_header_left = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
        })
        line_header_left_total = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
            'top': True,
            'bottom': True,
        })
        line_header_light = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
        })
        line_header_light_total = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'top': True,
            'bottom': True,
        })
        line_header_light_left = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
        })
        line_header_highlight = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
        })
        line_header_light_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
        })
        row_pos = 0
        row_pos_2 = 0
        sheet = workbook.add_worksheet('Trial Balance')
        sheet_2 = workbook.add_worksheet('Filters')
        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)

        sheet_2.set_column(0, 0, 35)
        sheet_2.set_column(1, 1, 25)
        sheet_2.set_column(2, 2, 25)
        sheet_2.set_column(3, 3, 25)
        sheet_2.set_column(4, 4, 25)
        sheet_2.set_column(5, 5, 25)
        sheet_2.set_column(6, 6, 25)

        sheet.freeze_panes(5, 0)

        sheet.set_zoom(80)

        sheet.screen_gridlines = False
        sheet_2.screen_gridlines = False
        sheet_2.protect()

        row = 1
        image = get_resource_path('dynamic_xlsx', 'static/description', 'logo.png')
        sheet.insert_image(row, 0, image,  {'x_scale': 0.2, 'y_scale': 0.2})

        # For Formating purpose
        lang = self.env.user.lang
        language_id = self.env['res.lang'].search([('code', '=', lang)])[0]
        self._format_float_and_dates(self.env.user.company_id.currency_id, language_id, line_header,line_header_light, line_header_highlight, line_header_light_date,format_merged_header_without_border)

        if record:

            data = record.read()
            date_from = record.date_from
            date_to = record.date_to
            x_month = date_to.strftime('%B')


            sheet.merge_range(0, 0, 0, 10, data[0]['company_id'][1], format_title)
            sheet.merge_range(1, 0, 2, 10, 'Trial Balance', format_title2)            

            sheet.merge_range(3, 0, 3, 10, 'From %s %s' % (date_from.strftime('%d %B %Y'), date_to.strftime('%d %B %Y')), format_title)
            
            dateformat = self.env.user.lang
            filters, account_lines, retained, subtotal = record.get_report_datas()

            # Filter section
            self.prepare_report_filters(data, filters, sheet_2, row_pos_2, language_id, format_header, line_header_light_date, content_header)
            # Content section
            self.prepare_report_contents(account_lines, retained, subtotal, filters, sheet, row_pos, language_id, format_merged_header, format_merged_header_without_border,
            format_header, line_header_light_left, line_header_light, line_header_highlight,line_header_left_total, line_header_light_total, line_header_total)