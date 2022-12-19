# _*_ coding: utf-8
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from io import BytesIO
import base64

try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
    from xlsxwriter.utility import xl_rowcol_to_cell
except ImportError:
    ReportXlsx = object

DATE_DICT = {
    "%m/%d/%Y": "mm/dd/yyyy",
    "%Y/%m/%d": "yyyy/mm/dd",
    "%m/%d/%y": "mm/dd/yy",
    "%d/%m/%Y": "dd/mm/yyyy",
    "%d/%m/%y": "dd/mm/yy",
    "%d-%m-%Y": "dd-mm-yyyy",
    "%d-%m-%y": "dd-mm-yy",
    "%m-%d-%Y": "mm-dd-yyyy",
    "%m-%d-%y": "mm-dd-yy",
    "%Y-%m-%d": "yyyy-mm-dd",
    "%f/%e/%Y": "m/d/yyyy",
    "%f/%e/%y": "m/d/yy",
    "%e/%f/%Y": "d/m/yyyy",
    "%e/%f/%y": "d/m/yy",
    "%f-%e-%Y": "m-d-yyyy",
    "%f-%e-%y": "m-d-yy",
    "%e-%f-%Y": "d-m-yyyy",
    "%e-%f-%y": "d-m-yy",
}


class InsFinancialReportXlsx(models.AbstractModel):
    _name = "report.dynamic_xlsx.ins_financial_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def _define_formats(self, workbook):
        """Add cell formats to current workbook.
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
        self.format_header = workbook.add_format(
            {
                "bold": True,
                "font_size": 10,
                "align": "center",
                "font": "Arial",
                "bottom": False,
            }
        )
        self.content_header = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "center",
                "font": "Arial",
            }
        )
        self.content_header_date = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "center",
                "font": "Arial",
            }
        )
        self.line_header = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "right",
                "font": "Arial",
                "bottom": False,
            }
        )
        self.line_header_bold = workbook.add_format(
            {
                "bold": True,
                "font_size": 10,
                "align": "right",
                "font": "Arial",
                "bottom": True,
            }
        )
        self.line_header_string = workbook.add_format(
            {
                "bold": False,
                "font_size": 10,
                "align": "left",
                "font": "Arial",
                "bottom": False,
            }
        )
        self.line_header_string_bold = workbook.add_format(
            {
                "bold": True,
                "font_size": 10,
                "align": "left",
                "font": "Arial",
                "bottom": True,
            }
        )

    def prepare_report_filters(self, filter, sheet_2, row_pos_2, language_id, content_header_date, format_header):
        """It is writing under second page"""
        row_pos_2 += 2
        if filter:
            # Date from
            sheet_2.write_string(
                row_pos_2, 0, _("Date from"), format_header
            )
            date = self.convert_to_date(language_id,
                filter["form"]["date_from"]
                and filter["form"]["date_from"].strftime("%Y-%m-%d")
            )
            if filter["form"].get("date_from"):
                sheet_2.write_datetime(
                    row_pos_2, 1, date, content_header_date
                )
            row_pos_2 += 1
            # Date to
            sheet_2.write_string(
                row_pos_2, 0, _("Date to"), format_header
            )
            date = self.convert_to_date(
                filter["form"]["date_to"]
                and filter["form"]["date_to"].strftime("%Y-%m-%d")
            )
#            if filter["form"].get("date_to"):
#                sheet_2.write_datetime(
#                    row_pos_2, 1, date, content_header_date
#                )
            row_pos_2 += 1
            if filter["form"]["enable_filter"]:
                # Compariosn Date from
                sheet_2.write_string(
                    row_pos_2, 0, _("Comparison Date from"), format_header
                )
                date = self.convert_to_date(
                    filter["form"]["comparison_context"]["date_from"]
                    and filter["form"]["comparison_context"]["date_from"].strftime(
                        "%Y-%m-%d"
                    )
                )
#                if filter["form"]["comparison_context"].get("date_from"):
#                    sheet_2.write_datetime(
#                        row_pos_2, 1, date, content_header_date
#                    )
                row_pos_2 += 1
                # Compariosn Date to
#                raise UserError(_('date %s\nheader_date %s')%(_("Comparison Date to"),content_header_date,))
                sheet_2.write_string(
                    row_pos_2, 0, _("Comparison Date to"), format_header
                )
                date = self.convert_to_date(
                    filter["form"]["comparison_context"]["date_to"]
                    and filter["form"]["comparison_context"]["date_to"].strftime(
                        "%Y-%m-%d"
                    )
                )
#                raise UserError(_('date %s\nheader_date %s')%(date,content_header_date,))
                if date: #filter["form"]["comparison_context"].get("date_to"):
                    sheet_2.write_datetime(
                        row_pos_2, 1, date, content_header_date
                    )

    def prepare_report_contents(self, data, sheet,  row_pos, format_header, line_header, line_header_string, line_header_string_bold, line_header_bold):
        row_pos += 3

        if data["form"]["debit_credit"] == 1:

            sheet.set_column(0, 0, 90)
            sheet.set_column(1, 1, 15)
            sheet.set_column(2, 3, 15)
            sheet.set_column(3, 3, 15)
            sheet.set_column(4, 3, 15)

            sheet.write_string(row_pos, 0, _("Name"), format_header)
            sheet.write_string(row_pos, 1, _("Initial Balance"), format_header)
            sheet.write_string(row_pos, 2, _("Debit"), format_header)
            sheet.write_string(row_pos, 3, _("Credit"), format_header)
            sheet.write_string(row_pos, 4, _("Balance"), format_header)

            for a in data["report_lines"]:
                if a["level"] == 2:
                    row_pos += 1
                row_pos += 1
                if a.get("account", False):
                    tmp_style_str = line_header_string
                    tmp_style_num = line_header
                else:
                    tmp_style_str = line_header_string_bold
                    tmp_style_num = line_header_bold
                sheet.write_string(
                    row_pos,
                    0,
                    "   " * len(a.get("list_len", [])) + a.get("name"),
                    tmp_style_str,
                )
                sheet.write_number(
                    row_pos, 1, float(a.get("balance_init")), tmp_style_num
                )
                if a.get("debit")!=None:
                    sheet.write_number(
                        row_pos, 2, float(a.get("debit")), tmp_style_num
                    )
                if a.get("credit")!=None:
                    sheet.write_number(
                        row_pos, 3, float(a.get("credit")), tmp_style_num
                    )
                sheet.write_number(
                    row_pos, 4, float(a.get("balance")), tmp_style_num
                )

        if data["form"]["debit_credit"] != 1:

            sheet.set_column(0, 0, 105)
            sheet.set_column(1, 1, 15)
            sheet.set_column(2, 2, 15)
            sheet.set_column(3, 3, 15)

            sheet.write_string(row_pos, 0, _("Name"), format_header)
            col_pos = 1
            if data["form"]["enable_budget_year"]:
                sheet.write_string(
                    row_pos, col_pos, "Anggaran " + data["form"]["label_budget_year"], format_header
                )
                col_pos +=1
            if data["form"]["enable_budget_month"]:
                sheet.write_string(
                    row_pos, col_pos, "Anggaran " + data["form"]["label_balance"], format_header
                )
                col_pos +=1
            if data["form"]["enable_filter"]:
                sheet.write_string(
                    row_pos, col_pos, data["form"]["label_filter"], format_header
                )
#                sheet.write_string(
#                    row_pos, 2, _("Initial Balance"), format_header
#                )
                sheet.write_string(
                    row_pos, col_pos+1, data["form"]["label_balance"], format_header
                )
                col_pos +=2
            else:
                sheet.write_string(
                    row_pos, col_pos, _("Initial Balance"), format_header
                )
                sheet.write_string(
                    row_pos, col_pos+1, _("Balance"), format_header
                )
                col_pos +=2

            for a in data["report_lines"]:
                if a["level"] == 2:
                    row_pos += 1
                row_pos += 1
                if a.get("account", False):
                    tmp_style_str = line_header_string
                    tmp_style_num = line_header
                else:
                    tmp_style_str = line_header_string_bold
                    tmp_style_num = line_header_bold
                sheet.write_string(
                    row_pos,
                    0,
                    "   " * len(a.get("list_len", [])) + a.get("name"),
                    tmp_style_str,
                )
                col_pos = 1
                if data["form"]["enable_budget_year"]:
                    sheet.write_number(
                        row_pos, col_pos, float(a.get("balance_budget_year")), tmp_style_num
                    )
                    col_pos +=1
                if data["form"]["enable_budget_month"]:
                    sheet.write_number(
                        row_pos, col_pos, float(a.get("balance_budget_month")), tmp_style_num
                    )
                    col_pos +=1
                if data["form"]["enable_filter"]:
                    sheet.write_number(
                        row_pos, col_pos, float(a.get("balance_prev")), tmp_style_num
                    )
#                    sheet.write_number(
#                        row_pos, 2, float(a.get("balance_init")), tmp_style_num
#                    )
                    sheet.write_number(
                        row_pos, col_pos+1, float(a.get("balance")), tmp_style_num
                    )
                else:
                    sheet.write_number(
                        row_pos, col_pos, float(a.get("balance_init")), tmp_style_num
                    )
                    sheet.write_number(
                        row_pos, col_pos+1, float(a.get("balance")), tmp_style_num
                    )

        if (
            data.get("initial_balance")
            or data.get("current_balance")
            or data.get("ending_balance")
        ):
            row_pos += 2
            sheet.merge_range(
                row_pos, 1, row_pos, 2, "Initial Cash Balance", tmp_style_num
            )
            sheet.write_number(
                row_pos, 3, float(data.get("initial_balance")), tmp_style_num
            )
            row_pos += 1
            sheet.merge_range(
                row_pos, 1, row_pos, 2, "Current Cash Balance", tmp_style_num
            )
            sheet.write_number(
                row_pos, 3, float(data.get("current_balance")), tmp_style_num
            )
            row_pos += 1
            sheet.merge_range(
                row_pos, 1, row_pos, 2, "Net Cash Balance", tmp_style_num
            )
            sheet.write_number(
                row_pos, 3, float(data.get("ending_balance")), tmp_style_num
            )

    def _format_float_and_dates(self, currency_id, lang_id, line_header, line_header_bold, content_header_date):

        line_header.num_format = currency_id.excel_format
        line_header_bold.num_format = currency_id.excel_format

        content_header_date.num_format = DATE_DICT.get(
            lang_id.date_format, "dd/mm/yyyy"
        )

    def convert_to_date(self, language_id, datestring=False):
        if datestring:
            datestring = fields.Date.from_string(datestring).strftime(
                language_id.date_format
            )
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
        row_pos = 0
        row_pos_2 = 0

        if not record:
            return False
        data = record.get_report_values()
        date_to = record.date_to

#        self.record = record  # Wizard object

        sheet = workbook.add_worksheet(data["form"]["account_report_id"][1])
        sheet_2 = workbook.add_worksheet("Filters")

        sheet_2.set_column(0, 0, 25)
        sheet_2.set_column(1, 1, 25)
        sheet_2.set_column(2, 2, 25)
        sheet_2.set_column(3, 3, 25)
        sheet_2.set_column(4, 4, 25)
        sheet_2.set_column(5, 5, 25)
        sheet_2.set_column(6, 6, 25)

        sheet.freeze_panes(4, 0)

        sheet.screen_gridlines = False
        sheet_2.screen_gridlines = False
        # sheet.protect()
        sheet_2.protect()

        # For Formating purpose
        lang = self.env.user.lang
        language_id = self.env["res.lang"].search([("code", "=", lang)])[0]
        self._format_float_and_dates(
            self.env.user.company_id.currency_id, language_id, line_header, line_header_bold, content_header_date
        )
        user = self.env["res.users"].browse(self.env.uid)
        partner = self.env["res.partner"].browse(user.company_id.id)
#        logo = BytesIO(base64.b64decode(partner.image))
#        sheet.insert_image(
#            0, 0, "logo.png", {"image_data": logo, "x_scale": 0.35, "y_scale": 0.3}
#        )

        sheet.merge_range(
            0,
            0,
            0,
            3,
            data["form"]["company_id"][1],
            format_title,
        )
        sheet.merge_range(
            1, 0, 1, 3, "Balance Sheet (Standard)", format_title2
        )
        sheet.merge_range(
            2, 0, 2, 3, "As of %s" % (date_to.strftime("%d %b %Y")), format_title
        )

        dateformat = self.env.user.lang

        # Filter section
        self.prepare_report_filters(data, sheet_2, row_pos_2, language_id, content_header_date, format_header)
        # Content section
        self.prepare_report_contents(data, sheet, row_pos,format_header,line_header,line_header_bold,line_header_string_bold,line_header_bold)
