# _*_ coding: utf-8
from odoo import models, fields, api, _

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

class InsGeneralLedgerXlsx(models.AbstractModel):
    _name = 'report.dynamic_xlsx.ins_general_ledger_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Available formats:
         * format_title
         * format_header
        """
        self.format_title = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "font_size": 11,
                "border": False,
                "font": "Arial",
            }
        )
        self.format_title2 = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "font_size": 15,
                "border": False,
                "font": "Arial",
                "font_color": "red",
                "valign": "center",
            }
        )
        format_header = workbook.add_format(
            {
                "bold": True,
                "font_size": 10,
                "align": "center",
                "font": "Arial",
                "bottom": False,
            }
        )
        content_header = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "center",
                "font": "Arial",
            }
        )
        content_header_date = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "center",
                "font": "Arial",
            }
        )
        line_header = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "right",
                "font": "Arial",
                "bottom": False,
            }
        )
        line_header_bold = workbook.add_format(
            {
                "bold": True,
                "font_size": 10,
                "align": "right",
                "font": "Arial",
                "bottom": True,
            }
        )
        line_header_string = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "left",
                "font": "Arial",
                "bottom": False,
            }
        )
        line_header_string_bold = workbook.add_format(
            {
                "bold": True,
                "font_size": 10,
                "align": "left",
                "font": "Arial",
                "bottom": True,
            }
        )

    def prepare_report_filters(self, filter, row_pos_2, sheet_2, format_header, language_id, content_header_date, content_header):
        """It is writing under second page"""
        row_pos_2 += 2
        if filter:
            # Date from
            sheet_2.write_string(row_pos_2, 0, _('Date from'),
                                    format_header)
            sheet_2.write_datetime(row_pos_2, 1, self.convert_to_date(str(filter['date_from']) or '', language_id),
                                    content_header_date)
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Date to'),
                                    format_header)
            sheet_2.write_datetime(row_pos_2, 1, self.convert_to_date(str(filter['date_to']) or '', language_id),
                                    content_header_date)
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Target moves'),
                                    format_header)
            sheet_2.write_string(row_pos_2, 1, filter['target_moves'],
                                    content_header)
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Display accounts'),
                                    format_header)
            sheet_2.write_string(row_pos_2, 1, filter['display_accounts'],
                                    content_header)
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Sort by'),
                                    format_header)
            sheet_2.write_string(row_pos_2, 1, filter['sort_accounts_by'],
                                    content_header)
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Initial Balance'),
                                    format_header)
            sheet_2.write_string(row_pos_2, 1, filter['initial_balance'],
                                    content_header)
            row_pos_2 += 1

            # Journals
            row_pos_2 += 2
            sheet_2.write_string(row_pos_2, 0, _('Journals'),
                                    format_header)
            j_list = ', '.join([lt or '' for lt in filter.get('journals')])
            sheet_2.write_string(row_pos_2, 1, j_list,
                                      content_header)

            # Partners
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Partners'),
                                                 format_header)
            p_list = ', '.join([lt or '' for lt in filter.get('partners')])
            sheet_2.write_string(row_pos_2, 1, p_list,
                                      content_header)

            # Accounts
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Accounts'),
                                    format_header)
            a_list = ', '.join([lt or '' for lt in filter.get('accounts')])
            sheet_2.write_string(row_pos_2, 1, a_list,
                                      content_header)

            # Account Tags
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Account Tags'),
                                      format_header)
            a_list = ', '.join([lt or '' for lt in filter.get('account_tags')])
            sheet_2.write_string(row_pos_2, 1, a_list,
                                      content_header)

            # Analytic Accounts
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Analytic Accounts'),
                                      format_header)
            a_list = ', '.join([lt or '' for lt in filter.get('analytics')])
            sheet_2.write_string(row_pos_2, 1, a_list,
                                      content_header)

            # Analytic Tags
            row_pos_2 += 1
            sheet_2.write_string(row_pos_2, 0, _('Analytic Tags'),
                                      format_header)
            a_list = ', '.join([lt or '' for lt in filter.get('analytic_tags')])
            sheet_2.write_string(row_pos_2, 1, a_list,
                                      content_header)

    def prepare_report_contents(self, record, data, acc_lines, filter, row_pos, sheet, line_header, line_header_light,line_header_light_initial,line_header_light_ending, line_header_light_date, content_header_date, format_header, language_id):
        data = data[0]
        row_pos += 3

        if filter.get('include_details', False):
            sheet.write_string(row_pos, 0, _('Date'),
                                    format_header)
            sheet.write_string(row_pos, 1, _('JRNL'),
                                    format_header)
            sheet.write_string(row_pos, 2, _('Partner'),
                                    format_header)
            # sheet.write_string(row_pos, 3, _('Ref'),
            #                         format_header)
            sheet.write_string(row_pos, 3, _('Move'),
                                    format_header)
            sheet.write_string(row_pos, 4, _('Entry Label'),
                                    format_header)
            sheet.write_string(row_pos, 5, _('Debit'),
                                    format_header)
            sheet.write_string(row_pos, 6, _('Credit'),
                                    format_header)
            sheet.write_string(row_pos, 7, _('Balance'),
                                    format_header)
        else:
            sheet.merge_range(row_pos, 0, row_pos, 1, _('Code'), format_header)
            sheet.merge_range(row_pos, 2, row_pos, 4, _('Account'), format_header)
            sheet.write_string(row_pos, 5, _('Debit'),
                                    format_header)
            sheet.write_string(row_pos, 6, _('Credit'),
                                    format_header)
            sheet.write_string(row_pos, 7, _('Balance'),
                                    format_header)

        if acc_lines:
            for line in acc_lines:
                row_pos += 1
                sheet.merge_range(row_pos, 0, row_pos, 4, '            ' + acc_lines[line].get('code') + ' - ' + acc_lines[line].get('name'), line_header)
                sheet.write_number(row_pos, 5, float(acc_lines[line].get('debit')), line_header)
                sheet.write_number(row_pos, 6, float(acc_lines[line].get('credit')), line_header)
                sheet.write_number(row_pos, 7, float(acc_lines[line].get('balance')), line_header)

                if filter.get('include_details', False):
                    account_id = acc_lines[line].get('id')
                    count, offset, sub_lines = record.build_detailed_move_lines(offset=0, account=account_id,
                                                                                     fetch_range=1000000)

                    for sub_line in sub_lines:
                        if sub_line.get('move_name') == 'Initial Balance':
                            row_pos += 1
                            sheet.write_string(row_pos, 4, sub_line.get('move_name'),
                                                    line_header_light_initial)
                            sheet.write_number(row_pos, 5, float(acc_lines[line].get('debit')),
                                                    line_header_light_initial)
                            sheet.write_number(row_pos, 6, float(acc_lines[line].get('credit')),
                                                    line_header_light_initial)
                            sheet.write_number(row_pos, 7, float(acc_lines[line].get('balance')),
                                                    line_header_light_initial)
                        elif sub_line.get('move_name') not in ['Initial Balance','Ending Balance']:
                            row_pos += 1
                            sheet.write_datetime(row_pos, 0, self.convert_to_date(sub_line.get('ldate'), language_id),
                                                    line_header_light_date)
                            sheet.write_string(row_pos, 1, sub_line.get('lcode'),
                                                    line_header_light)
                            sheet.write_string(row_pos, 2, sub_line.get('partner_name') or '',
                                                    line_header_light)
                            # sheet.write_string(row_pos, 3, sub_line.get('lref') or '',
                            #                         line_header_light)
                            sheet.write_string(row_pos, 3, sub_line.get('move_name'),
                                                    line_header_light)
                            sheet.write_string(row_pos, 4, sub_line.get('lname') or '',
                                                    line_header_light)
                            sheet.write_number(row_pos, 5,
                                                    float(sub_line.get('debit')),line_header_light)
                            sheet.write_number(row_pos, 6,
                                                    float(sub_line.get('credit')),line_header_light)
                            sheet.write_number(row_pos, 7,
                                                    float(sub_line.get('balance')),line_header_light)
                        else: # Ending Balance
                            row_pos += 1
                            sheet.write_string(row_pos, 4, sub_line.get('move_name'),
                                                    line_header_light_ending)
                            sheet.write_number(row_pos, 5, float(acc_lines[line].get('debit')),
                                                    line_header_light_ending)
                            sheet.write_number(row_pos, 6, float(acc_lines[line].get('credit')),
                                                    line_header_light_ending)
                            sheet.write_number(row_pos, 7, float(acc_lines[line].get('balance')),
                                                    line_header_light_ending)

    def _format_float_and_dates(self, currency_id, lang_id, line_header, line_header_light,line_header_light_initial,line_header_light_ending, line_header_light_date, content_header_date):

        line_header.num_format = currency_id.excel_format
        line_header_light.num_format = currency_id.excel_format
        line_header_light_initial.num_format = currency_id.excel_format
        line_header_light_ending.num_format = currency_id.excel_format


        line_header_light_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')
        content_header_date.num_format = DATE_DICT.get(lang_id.date_format, 'dd/mm/yyyy')

        return  line_header, line_header_light,line_header_light_initial,line_header_light_ending, line_header_light_date, content_header_date

    def convert_to_date(self, datestring=False, language_id=False):
        if datestring:
            datestring = fields.Date.from_string(datestring).strftime(language_id.date_format)
            return datetime.strptime(datestring, language_id.date_format)
        else:
            return False

    def generate_xlsx_report(self, workbook, data, record):

#        self._define_formats(workbook)
        format_title = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "font_size": 11,
                "border": False,
                "font": "Arial",
            }
        )
        format_title2 = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "font_size": 15,
                "border": False,
                "font": "Arial",
                "font_color": "red",
                "valign": "center",
            }
        )
        format_header = workbook.add_format(
            {
                "bold": True,
                "font_size": 10,
                "align": "center",
                "font": "Arial",
                "bottom": False,
            }
        )
        content_header = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "center",
                "font": "Arial",
            }
        )
        content_header_date = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "center",
                "font": "Arial",
            }
        )
        line_header = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "right",
                "font": "Arial",
                "bottom": False,
            }
        )
        line_header_bold = workbook.add_format(
            {
                "bold": True,
                "font_size": 10,
                "align": "right",
                "font": "Arial",
                "bottom": True,
            }
        )
        line_header_light = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "left",
                "font": "Arial",
                "bottom": False,
            }
        )
        line_header_light_date = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "left",
                "font": "Arial",
                "bottom": False,
            }
        )
        line_header_light_ending = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "left",
                "font": "Arial",
                "bottom": False,
            }
        )
        line_header_light_initial = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "left",
                "font": "Arial",
                "bottom": False,
            }
        )
        line_header_string_bold = workbook.add_format(
            {
                "bold": True,
                "font_size": 10,
                "align": "left",
                "font": "Arial",
                "bottom": True,
            }
        )

        row_pos = 0
        row_pos_2 = 0

#        self.record = record # Wizard object

        sheet = workbook.add_worksheet('General Ledger')
        sheet_2 = workbook.add_worksheet('Filters')
        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 18)
        sheet.set_column(4, 4, 30)
        sheet.set_column(5, 5, 10)
        sheet.set_column(6, 6, 10)
        sheet.set_column(7, 7, 10)

        sheet_2.set_column(0, 0, 35)
        sheet_2.set_column(1, 1, 25)
        sheet_2.set_column(2, 2, 25)
        sheet_2.set_column(3, 3, 25)
        sheet_2.set_column(4, 4, 25)
        sheet_2.set_column(5, 5, 25)
        sheet_2.set_column(6, 6, 25)

        sheet.freeze_panes(4, 0)

        sheet.screen_gridlines = False
        sheet_2.screen_gridlines = False
        sheet_2.protect()

        # For Formating purpose
        lang = self.env.user.lang
        language_id = self.env['res.lang'].search([('code','=',lang)])[0]
        line_header, line_header_light,line_header_light_initial,line_header_light_ending, line_header_light_date, content_header_date = self._format_float_and_dates(self.env.user.company_id.currency_id, language_id, line_header, line_header_light,line_header_light_initial,line_header_light_ending, line_header_light_date, content_header_date)

        if record:
            data = record.read()
            sheet.merge_range(0, 0, 0, 8, 'General Ledger'+' - '+data[0]['company_id'][1], format_title)
            dateformat = self.env.user.lang
            filters, account_lines = record.get_report_datas()
            # Filter section
            self.prepare_report_filters(filters,row_pos_2,sheet_2, format_header, language_id, content_header_date, content_header)
            # Content section
            self.prepare_report_contents(record, data, account_lines, filters, row_pos, sheet, line_header, line_header_light,line_header_light_initial,line_header_light_ending, line_header_light_date, content_header_date, format_header, language_id)
