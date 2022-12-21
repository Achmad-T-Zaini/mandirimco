# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import re
from datetime import datetime, timedelta, date
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class InsFinancialReport(models.TransientModel):
    _name = "ins.financial.report"
    _description = "Financial Reports"

    @api.onchange("company_id")
    def _onchange_company_id(self):
        if self.company_id:
            self.journal_ids = self.env["account.journal"].search(
                [("company_id", "=", self.company_id.id)]
            )
        else:
            self.journal_ids = self.env["account.journal"].search([])

    @api.onchange("date_range", "financial_year")
    def onchange_date_range(self):
        if self.date_range:
            date = datetime.today()
            if self.date_range == "today":
                self.date_from = date.strftime("%Y-%m-%d")
                self.date_to = date.strftime("%Y-%m-%d")
            if self.date_range == "this_week":
                day_today = date - timedelta(days=date.weekday())
                self.date_from = (day_today - timedelta(days=date.weekday())).strftime(
                    "%Y-%m-%d"
                )
                self.date_to = (day_today + timedelta(days=6)).strftime("%Y-%m-%d")
            if self.date_range == "this_month":
                self.date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
                self.date_to = datetime(
                    date.year, date.month, calendar.mdays[date.month]
                ).strftime("%Y-%m-%d")
            if self.date_range == "this_quarter":
                if int((date.month - 1) / 3) == 0:  # First quarter
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 3, calendar.mdays[3]).strftime(
                        "%Y-%m-%d"
                    )
                if int((date.month - 1) / 3) == 1:  # Second quarter
                    self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 6, calendar.mdays[6]).strftime(
                        "%Y-%m-%d"
                    )
                if int((date.month - 1) / 3) == 2:  # Third quarter
                    self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 9, calendar.mdays[9]).strftime(
                        "%Y-%m-%d"
                    )
                if int((date.month - 1) / 3) == 3:  # Fourth quarter
                    self.date_from = datetime(date.year, 10, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, calendar.mdays[12]).strftime(
                        "%Y-%m-%d"
                    )
            if self.date_range == "this_financial_year":
                if self.financial_year == "january_december":
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, 31).strftime("%Y-%m-%d")
                if self.financial_year == "april_march":
                    if date.month < 4:
                        self.date_from = datetime(date.year - 1, 4, 1).strftime(
                            "%Y-%m-%d"
                        )
                        self.date_to = datetime(date.year, 3, 31).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 3, 31).strftime(
                            "%Y-%m-%d"
                        )
                if self.financial_year == "july_june":
                    if date.month < 7:
                        self.date_from = datetime(date.year - 1, 7, 1).strftime(
                            "%Y-%m-%d"
                        )
                        self.date_to = datetime(date.year, 6, 30).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 6, 30).strftime(
                            "%Y-%m-%d"
                        )
            date = datetime.now() - relativedelta(days=1)
            if self.date_range == "yesterday":
                self.date_from = date.strftime("%Y-%m-%d")
                self.date_to = date.strftime("%Y-%m-%d")
            date = datetime.now() - relativedelta(days=7)
            if self.date_range == "last_week":
                day_today = date - timedelta(days=date.weekday())
                self.date_from = (day_today - timedelta(days=date.weekday())).strftime(
                    "%Y-%m-%d"
                )
                self.date_to = (day_today + timedelta(days=6)).strftime("%Y-%m-%d")
            date = datetime.now() - relativedelta(months=1)
            if self.date_range == "last_month":
                self.date_from = datetime(date.year, date.month, 1).strftime("%Y-%m-%d")
                self.date_to = datetime(
                    date.year, date.month, calendar.mdays[date.month]
                ).strftime("%Y-%m-%d")
            date = datetime.now() - relativedelta(months=3)
            if self.date_range == "last_quarter":
                if int((date.month - 1) / 3) == 0:  # First quarter
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 3, calendar.mdays[3]).strftime(
                        "%Y-%m-%d"
                    )
                if int((date.month - 1) / 3) == 1:  # Second quarter
                    self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 6, calendar.mdays[6]).strftime(
                        "%Y-%m-%d"
                    )
                if int((date.month - 1) / 3) == 2:  # Third quarter
                    self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 9, calendar.mdays[9]).strftime(
                        "%Y-%m-%d"
                    )
                if int((date.month - 1) / 3) == 3:  # Fourth quarter
                    self.date_from = datetime(date.year, 10, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, calendar.mdays[12]).strftime(
                        "%Y-%m-%d"
                    )
            date = datetime.now() - relativedelta(years=1)
            if self.date_range == "last_financial_year":
                if self.financial_year == "january_december":
                    self.date_from = datetime(date.year, 1, 1).strftime("%Y-%m-%d")
                    self.date_to = datetime(date.year, 12, 31).strftime("%Y-%m-%d")
                if self.financial_year == "april_march":
                    if date.month < 4:
                        self.date_from = datetime(date.year - 1, 4, 1).strftime(
                            "%Y-%m-%d"
                        )
                        self.date_to = datetime(date.year, 3, 31).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 4, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 3, 31).strftime(
                            "%Y-%m-%d"
                        )
                if self.financial_year == "july_june":
                    if date.month < 7:
                        self.date_from = datetime(date.year - 1, 7, 1).strftime(
                            "%Y-%m-%d"
                        )
                        self.date_to = datetime(date.year, 6, 30).strftime("%Y-%m-%d")
                    else:
                        self.date_from = datetime(date.year, 7, 1).strftime("%Y-%m-%d")
                        self.date_to = datetime(date.year + 1, 6, 30).strftime(
                            "%Y-%m-%d"
                        )

    def _compute_account_balance(self, accounts, enable_budget_month, enable_budget_year = False):
        """compute the balance, debit and credit for the provided accounts"""
        mapping = {
            "balance": "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            "debit": "COALESCE(SUM(debit), 0) as debit",
            "credit": "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict.fromkeys(mapping, 0.0)
        if accounts:

            domain_warehouse = []
            if self.warehouse_ids:
                domain_warehouse = [("warehouse_id", "in", self.warehouse_ids.ids)]

            domain_department = []
            if self.department_ids:
                domain_department = [("department_id", "in", self.department_ids.ids)]

            tables, where_clause, where_params = self.env[
                "account.move.line"
            ]._query_get(domain_warehouse + domain_department)
#            raise UserError(_('tables %s\nwhere_clause %s\nwhere_param %s')%(tables, where_clause,where_params,))
            tables = tables.replace('"', "") if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = (
                "SELECT account_id as id, "
                + ", ".join(mapping.values())
                + " FROM "
                + tables
                + " WHERE account_id IN %s "
                + filters
#                + " AND date>=%s and date<=%s"
                + " GROUP BY account_id"
            )
            params = (tuple(accounts._ids),) + tuple(where_params)

########## Tambahan untuk Report Budget Compare
            if enable_budget_year:
                request = """
                            select abr.account_id as id,COALESCE(SUM(bl.planned_amount),0) as balance, 0 as debit,0 as credit 
                            from account_budget_rel abr
                            join budget_lines bl on bl.general_budget_id=abr.budget_id
                            where bl.date_from>=%s and bl.date_to<=%s and abr.account_id IN %s
                            group by abr.account_id
                        """
                params = (datetime.strptime(self.date_from.strftime("%Y-01-01"),"%Y-%m-%d").date(), datetime.strptime(self.date_from.strftime("%Y-12-31"),"%Y-%m-%d").date(), tuple(accounts._ids))
            elif enable_budget_month:
                request = """
                            select abr.account_id as id,COALESCE(SUM(bl.planned_amount),0) as balance, 0 as debit,0 as credit 
                            from account_budget_rel abr
                            join budget_lines bl on bl.general_budget_id=abr.budget_id
                            where bl.date_from>=%s and bl.date_to<=%s and abr.account_id IN %s
                            group by abr.account_id
                        """
                params = (self.date_from, self.date_to, tuple(accounts._ids))
########## End Tambahan untuk Report Budget Compare

#            raise UserError(_('req %s\nparam %s')%(request, params))
            self.env.cr.execute(request, params)

            res_query = self.env.cr.dictfetchall()
#            raise UserError(_('res %s')%(res_query))

            for row in res_query:
                res[row["id"]] = row
        return res

    def _compute_report_balance(self, reports, enable_budget_month, enable_budget_year,data_cye=False):
        """returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
        computed for this record. If the record is of type :
            'accounts' : it's the sum of the linked accounts
            'account_type' : it's the sum of leaf accoutns with such an account_type
            'account_report' : it's the amount of the related report
            'sum' : it's the sum of the children of this record (aka a 'view' record)"""
        res = {}
        fields = ["credit", "debit", "balance"]
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)

            if report.type == "accounts":
                # it's the sum of the linked accounts
                if self.account_report_id != self.env.ref(
                    "account_dynamic_reports.ins_account_financial_report_cash_flow0"
                ):
#                    if data_cye != False:
#                        raise UserError(_('cye %s')%(data_cye))
                    res[report.id]["account"] = self._compute_account_balance(
                        report.account_ids, enable_budget_month, enable_budget_year
                    )
                    for value in res[report.id]["account"].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
                else:
                    res2 = self._compute_report_balance(report.parent_id, enable_budget_month, enable_budget_year)
                    for key, value in res2.items():
                        if report in [
                            self.env.ref(
                                "account_dynamic_reports.ins_cash_in_operation_1"
                            ),
                            self.env.ref(
                                "account_dynamic_reports.ins_cash_in_investing_1"
                            ),
                            self.env.ref(
                                "account_dynamic_reports.ins_cash_in_financial_1"
                            ),
                        ]:
                            res[report.id]["debit"] += value["debit"]
                            res[report.id]["balance"] += value["debit"]
                        else:
                            res[report.id]["credit"] += value["credit"]
                            res[report.id]["balance"] += -(value["credit"])
            elif report.type == "account_type":
                # it's the sum the leaf accounts with such an account type
                if self.account_report_id != self.env.ref(
                    "account_dynamic_reports.ins_account_financial_report_cash_flow0"
                ):
                    accounts = self.env["account.account"].search(
                        [("user_type_id", "in", report.account_type_ids.ids)]
                    )
                    res[report.id]["account"] = self._compute_account_balance(accounts, enable_budget_month, enable_budget_year)
                    for value in res[report.id]["account"].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
                else:
                    accounts = self.env["account.account"].search(
                        [("user_type_id", "in", report.account_type_ids.ids)]
                    )
                    res[report.id]["account"] = self._compute_account_balance(accounts, enable_budget_month, enable_budget_year)
                    for value in res[report.id]["account"].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
            elif report.type == "account_report" and report.account_report_id:
                # it's the amount of the linked report
                if self.account_report_id != self.env.ref(
                    "account_dynamic_reports.ins_account_financial_report_cash_flow0"
                ):
                    res2 = self._compute_report_balance(report.account_report_id, enable_budget_month, enable_budget_year)
#                    raise UserError(_('res %s')%(res2,))
                    for key, value in res2.items():
                        for field in fields:
                            res[report.id][field] += value[field]
                else:
                    res[report.id]["account"] = self._compute_account_balance(
                        report.account_ids, enable_budget_month, enable_budget_year
                    )
                    for value in res[report.id]["account"].values():
                        for field in fields:
                            res[report.id][field] += value.get(field)
            elif report.type == "sum":
                # it's the sum of the children of this account.report
                if self.account_report_id != self.env.ref(
                    "account_dynamic_reports.ins_account_financial_report_cash_flow0"
                ):
                    res2 = self._compute_report_balance(report.children_ids, enable_budget_month, enable_budget_year)
                    for key, value in res2.items():
                        for field in fields:
                            res[report.id][field] += value[field]
#                    raise UserError(_('report %s-%s\n\nres2 %s\n\nres %s')%(report.name,report.children_ids,res2,res))
                else:
                    accounts = report.account_ids
                    if report == self.env.ref(
                        "account_dynamic_reports.ins_account_financial_report_cash_flow0"
                    ):
                        accounts = self.env["account.account"].search(
                            [
                                ("company_id", "=", self.env.user.company_id.id),
                                ("cash_flow_category", "not in", [0]),
                            ]
                        )
                    res[report.id]["account"] = self._compute_account_balance(accounts, enable_budget_month, enable_budget_year)
                    for values in res[report.id]["account"].values():
                        for field in fields:
                            res[report.id][field] += values.get(field)
        return res

    def get_account_lines(self, data, enable_budget_month, enable_budget_year, data_cye):
        lines = []
        initial_balance = 0.0
        current_balance = 0.0
        ending_balance = 0.0
        account_report = self.account_report_id
        child_reports = account_report._get_children_by_order()

        res = self.with_context(data.get("used_context"))._compute_report_balance(
            child_reports, enable_budget_month, enable_budget_year,data
        )

        cashflow_context = data.get("used_context")
        initial_to = fields.Date.from_string(
                data.get("used_context").get("date_from")
            ) - timedelta(days=1)
        cashflow_context.update(
                {"date_from": False, "date_to": fields.Date.to_string(initial_to)}
            )
        initial_res = self.with_context(cashflow_context)._compute_report_balance(child_reports, enable_budget_month,enable_budget_year)
#        raise UserError(_('initial_res %s')%(initial_res,))
        for report_id, value in initial_res.items():
            init_bal_temp = 0
            init_b = False
            report_acc = res[report_id].get("account")
            if report_acc:
                for account_id, val in (
                    initial_res[report_id].get("account").items()
                    ):
                    report_acc[account_id].update({"init_bal": 0})
                    init_account = self.env['account.account'].search([('id','=',int(account_id))])
                    init_b = init_account.user_type_id.include_initial_balance
#                    raise UserError(_('account_id %s == init_acc %s/%s')%(account_id,init_account,init_account.user_type_id.include_initial_balance))
                    if init_account.user_type_id.include_initial_balance:
                        if enable_budget_month or enable_budget_year:
                            report_acc[account_id].update({"init_bal": 0})
                        else:
                            report_acc[account_id].update({"init_bal": val["balance"]})
                            report_acc[account_id]["balance"]+=val["balance"]
                            init_bal_temp+=val["balance"]

            if enable_budget_month:
                res[report_id].update({"init_bal": 0})
            else:
                res[report_id].update({"init_bal": init_bal_temp})
                res[report_id]["balance"]+=init_bal_temp

#        raise UserError(_('res %s')%(res))
        if self.account_report_id == self.env.ref(
            "account_dynamic_reports.ins_account_financial_report_cash_flow0"
        ):
            cashflow_context = data.get("used_context")
            initial_to = fields.Date.from_string(
                data.get("used_context").get("date_from")
            ) - timedelta(days=1)
            cashflow_context.update(
                {"date_from": False, "date_to": fields.Date.to_string(initial_to)}
            )
            initial_balance = (
                self.with_context(cashflow_context)
                ._compute_report_balance(child_reports, enable_budget_month, enable_budget_year)
                .get(self.account_report_id.id)["balance"]
            )

            current_balance = res.get(self.account_report_id.id)["balance"]
            ending_balance = initial_balance + current_balance

        if data["enable_filter"]:
            comparison_res = self.with_context(
                data.get("comparison_context")
            )._compute_report_balance(child_reports, enable_budget_month, enable_budget_year)
#            raise UserError(_('comp res %s')%(comparison_res,))
            for report_id, value in comparison_res.items():
                res[report_id]["comp_bal"] = value["balance"]
                report_acc = res[report_id].get("account")
                if report_acc:
                    for account_id, val in (
                        comparison_res[report_id].get("account").items()
                    ):
                        report_acc[account_id]["comp_bal"] = val["balance"]

        for report in child_reports:
            company_id = self.env.user.company_id
            currency_id = company_id.currency_id
            vals = {
                "name": report.name,
                "balance": res[report.id]["balance"] * int(report.sign),
                "init_bal": res[report.id]["init_bal"] * int(report.sign),
                "parent": report.parent_id.id
                if report.parent_id.type in ["accounts", "account_type"]
                else 0,
                "self_id": report.id,
                "type": "report",
                "style_type": "main",
                "precision": currency_id.decimal_places,
                "symbol": currency_id.symbol,
                "position": currency_id.position,
                "list_len": [a for a in range(0, report.level)],
                "level": report.level,
                "company_currency_id": company_id.currency_id.id,
                "account_type": report.type
                or False,  # used to underline the financial report balances
                "sequence": 1000000000 + (report.sequence *100000000 / (10**report.level))
            }
            vals["debit"] = res[report.id]["debit"]
            vals["credit"] = res[report.id]["credit"]

            if data["enable_filter"]:
                vals["balance_cmp"] = res[report.id]["comp_bal"] * int(report.sign)
            
            vals["balance_init"] = res[report.id]["init_bal"] * int(report.sign)
            

            lines.append(vals)
            if report.display_detail == "no_detail":
                continue

            if res[report.id].get("account"):
                sub_lines = []
                for account_id, value in res[report.id]["account"].items():
                    flag = False
                    if data["display_zero_account"]:
                        flag = True
                    account = self.env["account.account"].browse(account_id)
                    vals = {
                        "account": account.id,
                        # "name": account.code + " " + account.name, ini yang diubah
                        "name": account.name,
                        "balance": value["balance"] * int(report.sign) or 0.0,
                        "init_bal": value["init_bal"] * int(report.sign) or 0.0,
                        "type": "account",
                        "parent": report.id
                        if report.type in ["accounts", "account_type"]
                        else 0,
                        "self_id": 50,
                        "style_type": "sub",
                        "precision": currency_id.decimal_places,
                        "symbol": currency_id.symbol,
                        "position": currency_id.position,
                        "list_len": [
                            a
                            for a in range(
                                0,
                                report.display_detail == "detail_with_hierarchy" and 4,
                            )
                        ],
                        "level": 4,
                        "company_currency_id": company_id.currency_id.id,
                        "account_type": account.internal_type,
                        "balance_prev": 0.0,
                        "balance_budget_month": 0.0,
                        "balance_budget_year": 0.0,
                        "sequence": 1000000000 + (report.sequence *100000000 / (10**report.level)) + account.id
                    }
                    vals["debit"] = value["debit"]
                    vals["credit"] = value["credit"]
                    flag = False

                    if not currency_id.is_zero(vals["balance"]):
                        flag = True
                    if data["enable_filter"]:
                        vals["balance_cmp"] = value["comp_bal"] * int(report.sign)
                        vals["balance_prev"] = 0
                        if not currency_id.is_zero(vals["balance_cmp"]):
                            flag = True
                    vals["balance_init"] = value["init_bal"] * int(report.sign)
                    if not currency_id.is_zero(vals["balance_init"]):
                        flag = True

                    if vals["account"]==self.env.user.company_id.current_year_earning_account.id:
                        data_bs = data.copy()
#                        data_cye = self.get_current_year_earning_values(data_bs,False)

                    if flag or vals["account"]==self.env.user.company_id.current_year_earning_account.id:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line["name"])
#                raise UserError(_('lines %s')%(lines,))
        #Perhtiungan Summary Info Report
#        raise UserError(_('initial_res %s\nlines %s')%(initial_res,lines,))
        for report in child_reports:
            if report.type=='sum':
                balance = debit = credit = balance_init = 0.0
                child_reps = self.env['ins.account.financial.report'].search([('type','in',['account_type','accounts','account_report']),('id','child_of',report.id)])
                for rep in child_reps:
                    c_line = list(filter(lambda l: l['name'] == rep.name, lines))
                    if rep.name==c_line[0]['name']:
                        balance_init += c_line[0]['balance_init'] 
                        balance += c_line[0]['balance_init'] + c_line[0]['debit'] -c_line[0]['credit']
 
                n_line = list(filter(lambda l: l['name'] == report.name, lines))
                n_line[0]['balance_init'] = balance_init * int(report.sign)
                n_line[0]['balance'] = balance * int(report.sign)
#                raise UserError(_('%s == %s = %s')%(report.name,n_line[0]['name'],balance_init,))

            elif report.type=='info':
                balance = debit = credit = balance_init = 0.0
                summ_data = {}
                for child in report.summary_lines:
                    c_line = list(filter(lambda l: l['name'] == child.name, lines))
                    if child.name==c_line[0]['name']:

#                    raise UserError(_('c_line %s \nchild %s')%(c_line[0]['name'],child.name))
                        balance_init += c_line[0]['balance_init'] 
                        balance += c_line[0]['balance']
                        debit += c_line[0]['debit']
                        credit += c_line[0]['credit']
                
                n_line = list(filter(lambda l: l['name'] == report.name, lines))
                n_line[0]['balance_init'] = balance_init * int(report.sign)
                n_line[0]['balance'] = balance * int(report.sign) #balance
                n_line[0]['debit'] = debit
                n_line[0]['credit'] = credit
                
#                raise UserError(_('lines %s\ninit %s\ncurr %s\nend %s')%(lines, initial_balance, current_balance, ending_balance,))
        return lines, initial_balance, current_balance, ending_balance

    def get_report_values(self,jenis=False):
        self.ensure_one()
        self.onchange_date_range()
        company_domain = [("company_id", "=", self.env.user.company_id.id)]
        journal_ids = self.env["account.journal"].search(company_domain)
        analytics = self.env["account.analytic.account"].search(company_domain)
        warehouses = self.env["stock.warehouse"].search(company_domain)
        departments = self.env["hr.department"].search(company_domain)
        analytic_tags = (
            self.env["account.analytic.tag"]
            .sudo()
            .search(
                [
                    "|",
                    ("company_id", "=", self.env.user.company_id.id),
                    ("company_id", "=", False),
                ]
            )
        )

        data = dict()
        data["ids"] = self.env.context.get("active_ids", [])
        data["model"] = self.env.context.get("active_model", "ir.ui.menu")
        data["form"] = self.read(
            [
                "date_from",
                "enable_filter",
                "debit_credit",
                "date_to",
                "date_range",
                "account_report_id",
                "target_moves",
                "view_format",
                "journal_ids",
                "display_zero_account",
                "analytic_ids",
                "warehouse_ids",
                "department_ids",
                "analytic_tag_ids",
                "company_id",
                "enable_filter",
                "date_from_cmp",
                "date_to_cmp",
                "label_filter",
                "filter_cmp",
                "label_balance",
                "enable_budget",
                "enable_budget_month",
                "enable_budget_year",
            ]
        )[0]
        data["form"].update({"journals_list": [(j.id, j.name) for j in journal_ids]})
        data["form"].update({"analytics_list": [(j.id, j.name) for j in analytics]})
        data["form"].update({"warehouse_list": [(j.id, j.name) for j in warehouses]})
        data["form"].update({"department_list": [(j.id, j.name) for j in departments]})

        data["form"].update(
            {"analytic_tag_list": [(j.id, j.name) for j in analytic_tags]}
        )

        if self.enable_filter:
            data["form"]["debit_credit"] = False

        date_from, date_to = self.date_from, self.date_to
        used_context = {}
        used_context["date_from"] = self.date_from or False
        used_context["date_to"] = self.date_to or False
        used_context["target_moves"] = self.target_moves

        used_context["strict_range"] = True
        used_context["company_id"] = self.env.user.company_id.id

        used_context["journal_ids"] = self.journal_ids.ids
        used_context["analytic_account_ids"] = self.analytic_ids
        used_context["warehouse_ids"] = self.warehouse_ids
        used_context["department_ids"] = self.department_ids
        used_context["analytic_tag_ids"] = self.analytic_tag_ids
        used_context["state"] = data["form"].get("target_moves", "")
        data["form"]["used_context"] = used_context

        comparison_context = {}
        comparison_context["strict_range"] = True
        comparison_context["company_id"] = self.env.user.company_id.id

        comparison_context["journal_ids"] = self.journal_ids.ids
        comparison_context["analytic_account_ids"] = self.analytic_ids
        comparison_context["warehouse_ids"] = self.warehouse_ids
        comparison_context["department_ids"] = self.department_ids
        comparison_context["analytic_tag_ids"] = self.analytic_tag_ids
        if self.filter_cmp == "filter_date":
            comparison_context["date_to"] = self.date_to_cmp or False
            comparison_context["date_from"] = self.date_from_cmp or False
#            comparison_context["date_to"] = False
#            comparison_context["date_from"] = False
        else:
            comparison_context["date_to"] = False
            comparison_context["date_from"] = False

        comparison_context["state"] = self.target_moves or ""
        data["form"]["comparison_context"] = comparison_context

        data_cmp = data_budget_month = data_budget_year =False
        if self.enable_budget:
            if self.enable_budget_month:
                data["form"]["enable_budget_month"] = self.enable_budget_month
                data_b = data.copy()
                data_budget_month = self.get_cmp_report_values(data_b,self.enable_budget_month)
            if self.enable_budget_year:
                data["form"]["enable_budget_year"] = self.enable_budget_year
                data_by = data.copy()
                data_by['form']['used_context']['date_from'] = datetime.strptime(self.date_from.strftime("%Y-01-01"),"%Y-%m-%d").date()
                data_budget_year = self.get_cmp_report_values(data_by,self.enable_budget_month,self.enable_budget_year)
            data['form']['enable_filter'] = False
            data['form']['date_from_cmp'] = False
            data['form']['date_to_cmp'] = False
            data['form']['used_context']['date_from'] = self.date_from
            data['form']['used_context']['date_to'] = self.date_to

        elif self.enable_filter:
            data['form']['date_from'] = self.date_from_cmp
            data['form']['date_to'] = self.date_to_cmp
            data['form']['enable_filter'] = False
            data['form']['date_from_cmp'] = False
            data['form']['date_to_cmp'] = False

            enable_filter = self.enable_filter
            date_from_cmp = self.date_from_cmp
            date_to_cmp = self.date_to_cmp
            date_from = self.date_from
            date_to = self.date_to
        
            self.enable_filter = False
            self.date_from = self.date_from_cmp
            self.date_to = self.date_to_cmp
            self.date_from_cmp = False
            self.date_to_cmp = False

            data['form']['used_context']['date_from'] = self.date_from
            data['form']['used_context']['date_to'] = self.date_to

            data_c = data.copy()
            data_cmp = self.get_cmp_report_values(data_c,False)
            self.enable_filter = True
            self.date_from = date_from
            self.date_to = date_to
            self.date_from_cmp = date_from_cmp
            self.date_to_cmp = date_to_cmp
#            data['form']['enable_filter'] = True

            data['form']['date_from'] = date_from
            data['form']['date_to'] = date_to
            data['form']['date_from_cmp'] = date_from_cmp
            data['form']['date_to_cmp'] = date_to_cmp
            data['form']['enable_filter'] = enable_filter

            data['form']['used_context']['date_from'] = date_from
            data['form']['used_context']['date_to'] = date_to

#        raise UserError(_('data %s')%(data["form"],))
        (
            report_lines,
            initial_balance,
            current_balance,
            ending_balance,
        ) = self.get_account_lines(data.get("form"),False,False,False)
        company_id = self.env.user.company_id
        data["currency"] = company_id.currency_id.id
        data["report_lines"] = report_lines
        data["initial_balance"] = initial_balance or 0.0
        data["current_balance"] = current_balance or 0.0
        data["ending_balance"] = ending_balance or 0.0

        for rec in data["report_lines"]:
            rec['balance_prev'] = 0.0
            rec['balance_budget_month'] = 0.0
            rec['balance_budget_year'] = 0.0
#        raise UserError(_('data %s')%(data["report_lines"],))

        if self.enable_filter:
            data['form']['enable_filter'] = True

        if self.enable_budget:
            if data_budget_year:
                data['form']['label_budget_year'] = 'Tahun ' + self.label_balance[-4:]
                for rec in data["report_lines"]:
                    report_sign = 1
                    report = False
                    rec['balance_budget_year'] = 0.0
                    if rec['type']!='account':
                        cdata = next(filter(lambda cdata: cdata.get('self_id') == rec['self_id'], data_budget_year['report_lines']), None)
                        report = self.env['ins.account.financial.report'].search([('id','=',rec['parent'])])
                    else:
                        cdata = next(filter(lambda cdata: cdata.get('account') == rec['account'], data_budget_year['report_lines']), None)
                        report = self.env['ins.account.financial.report'].search([('id','=',rec['self_id'])])

                    if cdata!=None:
                        if report:
                            report_sign = int(report.sign)
                        rec['balance_budget_year'] = cdata['balance'] * report_sign
            if data_budget_month:
                for rec in data["report_lines"]:
                    report_sign = 1
                    report = False
                    rec['balance_budget_month'] = 0.0
                    rec['comp_balance_month'] = 0.0
                    if rec['type']!='account':
                        cdata = next(filter(lambda cdata: cdata.get('self_id') == rec['self_id'], data_budget_month['report_lines']), None)
                        report = self.env['ins.account.financial.report'].search([('id','=',rec['parent'])])
                    else:
                        cdata = next(filter(lambda cdata: cdata.get('account') == rec['account'], data_budget_month['report_lines']), None)
                        report = self.env['ins.account.financial.report'].search([('id','=',rec['self_id'])])

                    if cdata!=None:
                        if report:
                            report_sign = int(report.sign)
                        rec['balance_budget_month'] = cdata['balance'] * report_sign
                        if rec['balance']!=0 and rec['balance_budget_month']!=0:
                            rec['comp_balance_month'] = round(rec['balance'] / rec['balance_budget_month'] * 100,2)
#                            raise UserError(_('data %s\ndata_budget_month %s\ncomp %s')%(rec['balance'],rec['balance_budget_month'],rec['balance'] / rec['balance_budget_month'] * 100,))
        if data_cmp:
            data['form']['comparison_context']['date_from'] = self.date_from_cmp
            data['form']['comparison_context']['date_to'] = self.date_to_cmp
            for rec in data["report_lines"]:
                report_sign = 1
                report = False
                rec['balance_prev'] = 0.0
                rec['balance_init_prev'] = 0.0
                if rec['type']!='account':
                    cdata = next(filter(lambda cdata: cdata.get('self_id') == rec['self_id'], data_cmp['report_lines']), None)
                    report = self.env['ins.account.financial.report'].search([('id','=',rec['parent'])])
                else:
                    cdata = next(filter(lambda cdata: cdata.get('account') == rec['account'], data_cmp['report_lines']), None)
                    report = self.env['ins.account.financial.report'].search([('id','=',rec['self_id'])])

                if cdata!=None:
                    if report:
                        report_sign = int(report.sign)
                    rec['balance_prev'] = cdata['balance'] * report_sign
                    rec['balance_init_prev'] = cdata['balance_init'] * report_sign

#        data_bs = data.copy()
#        data_cye = self.get_current_year_earning_values(data_bs,False)
#        data["form"]["current_year"] = data_cye


#        lines = data["report_lines"].sort(key=lambda k: k['sequence'])
        return data

    def get_cmp_report_values(self,data,enable_budget_month,enable_budget_year=False):
        (
            report_lines,
            initial_balance,
            current_balance,
            ending_balance,
        ) = self.get_account_lines(data.get("form"), enable_budget_month, enable_budget_year,False)
        company_id = self.env.user.company_id
        data["currency"] = company_id.currency_id.id
        data["report_lines"] = report_lines
        data["initial_balance"] = initial_balance or 0.0
        data["current_balance"] = current_balance or 0.0
        data["ending_balance"] = ending_balance or 0.0
        return data

    def get_current_year_earning_values(self,data,enable_budget_month,enable_budget_year=False):
        company_id = self.env.user.company_id
        used_context = data["used_context"]
        used_context["date_from"] = company_id.fiscalyear_lock_date + relativedelta(days=1) or False
        used_context["date_to"] = self.date_from + relativedelta(days=-1) or False
        data["used_context"] = used_context
        res = False
        (
            report_lines,
            initial_balance,
            current_balance,
            ending_balance,
        ) = self.get_account_lines(data, enable_budget_month, enable_budget_year,False)
        for rec in report_lines:
            if rec['type']=='report' and rec["account_type"]=="account_report":
                res = rec
                break

        return res

    @api.model
    def _get_default_report_id(self):
        if self.env.context.get("report_name", False):
            return self.env.context.get("report_name", False)
        return self.env.ref(
            "account_dynamic_reports.ins_account_financial_report_profitandloss0"
        ).id

    @api.model
    def _get_default_date_range(self):
        return self.env.user.company_id.date_range

    @api.model
    def _get_default_financial_year(self):
        return self.env.user.company_id.financial_year

    @api.model
    def _get_default_company(self):
        return self.env.user.company_id

    @api.depends("account_report_id")
    def name_get(self):
        res = []
        for record in self:
            name = record.account_report_id.name or "Financial Report"
            res.append((record.id, name))
        return res

    financial_year = fields.Selection(
        [
            ("april_march", "1 April to 31 March"),
            ("july_june", "1 july to 30 June"),
            ("january_december", "1 Jan to 31 Dec"),
        ],
        string="Financial Year",
        default=_get_default_financial_year,
    )

    date_range = fields.Selection(
        [
            ("today", "Today"),
            ("this_week", "This Week"),
            ("this_month", "This Month"),
            ("this_quarter", "This Quarter"),
            ("this_financial_year", "This financial Year"),
            ("yesterday", "Yesterday"),
            ("last_week", "Last Week"),
            ("last_month", "Last Month"),
            ("last_quarter", "Last Quarter"),
            ("last_financial_year", "Last Financial Year"),
        ],
        string="Date Range",
        default=_get_default_date_range,
    )
    view_format = fields.Selection(
        [("vertical", "Vertical"), ("horizontal", "Horizontal")],
        default="vertical",
        string="Format",
    )
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=_get_default_company
    )
    journal_ids = fields.Many2many(
        "account.journal",
        string="Journals",
        required=True,
        default=lambda self: self.env["account.journal"].search(
            [("company_id", "=", self.company_id.id)]
        ),
    )
    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")
    target_moves = fields.Selection(
        [
            ("posted", "All Posted Entries"),
            ("all", "All Entries"),
        ],
        string="Target Moves",
        required=True,
        default="posted",
    )

    display_zero_account = fields.Boolean(string="Display Zero Account", default=False)

    enable_filter = fields.Boolean(string="Enable Comparison", default=False)
    account_report_id = fields.Many2one(
        "ins.account.financial.report",
        string="Account Reports",
        required=True,
        default=_get_default_report_id,
    )

    debit_credit = fields.Boolean(
        string="Display Debit/Credit Columns",
        default=True,
        help="Help to identify debit and credit with balance line for better understanding.",
    )
    analytic_ids = fields.Many2many(
        "account.analytic.account", string="Analytic Accounts"
    )
    warehouse_ids = fields.Many2many("stock.warehouse", string="Warehouse")
    department_ids = fields.Many2many("hr.department", string="Department")
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")
    date_from_cmp = fields.Date(string="Start Date")
    date_to_cmp = fields.Date(string="End Date")
    filter_cmp = fields.Selection(
        [("filter_no", "No Filters"), ("filter_date", "Date")],
        string="Filter by",
        required=True,
        default="filter_date",
    )
    label_filter = fields.Char(
        string="Column Label",
        default="Comparison Period",
        help="This label will be displayed on report to show the balance computed for the given comparison filter.",
    )
    label_balance = fields.Char(
        string="Balance Label",
        default="Balance",
        help="This label will be displayed on report to show the balance computed.",
    )
    enable_budget = fields.Boolean(string="Budget Compare", default=False)
    enable_budget_year = fields.Boolean(string="Yearly Budget", default=False)
    enable_budget_month = fields.Boolean(string="Monthly Budget", default=False)

    @api.model
    def create(self, vals):
        ret = super(InsFinancialReport, self).create(vals)
        return ret

#    @api.multi
    def write(self, vals):
        if vals.get("date_range"):
            vals.update({"date_from": False, "date_to": False})
        if vals.get("date_from") and vals.get("date_to"):
            vals.update({"date_range": False})

        if vals.get("journal_ids"):
            vals.update({"journal_ids": [(4, j) for j in vals.get("journal_ids")]})
        if vals.get("journal_ids") == []:
            vals.update({"journal_ids": [(5,)]})

        if vals.get("analytic_ids"):
            vals.update({"analytic_ids": [(4, j) for j in vals.get("analytic_ids")]})
        if vals.get("analytic_ids") == []:
            vals.update({"analytic_ids": [(5,)]})

        if vals.get("warehouse_ids"):
            vals.update({"warehouse_ids": [(4, j) for j in vals.get("warehouse_ids")]})
        if vals.get("warehouse_ids") == []:
            vals.update({"warehouse_ids": [(5,)]})

        if vals.get("department_ids"):
            vals.update(
                {"department_ids": [(4, j) for j in vals.get("department_ids")]}
            )
        if vals.get("department_ids") == []:
            vals.update({"department_ids": [(5,)]})

        if vals.get("analytic_tag_ids"):
            vals.update(
                {"analytic_tag_ids": [(4, j) for j in vals.get("analytic_tag_ids")]}
            )
        if vals.get("analytic_tag_ids") == []:
            vals.update({"analytic_tag_ids": [(5,)]})

        ret = super(InsFinancialReport, self).write(vals)
        return ret

    def action_pdf(self):
        """ Button function for Pdf """
        data = self.get_report_values('pdf')
        data['form']['comparison_context']['date_from'] = self.date_from_cmp
        data['form']['comparison_context']['date_to'] = self.date_to_cmp
#        raise UserError(_('ndata %s')%(data["report_lines"],))
        return self.env.ref(
            "account_dynamic_reports.ins_financial_report_pdf"
        ).report_action(self, data)

    def action_xlsx(self):
        """ Button function for Xlsx """
        raise UserError(
            _(
                'Please install a free module "dynamic_xlsx".'
                'You can get it by contacting "pycustech@gmail.com". It is free'
            )
        )

    def action_view(self):
        res = {
            "type": "ir.actions.client",
            "name": "FR View",
            "tag": "dynamic.fr",
            "context": {
                "wizard_id": self.id,
                "account_report_id": self.account_report_id.id,
            },
        }
        return res

    @api.onchange('enable_filter', 'date_to','date_to_cmp', 'enable_budget')
    def _onchange_enable_filter(self):
        if self.enable_filter:
            if self.date_to:
                self.label_balance = self.date_to.strftime("%B %Y")
            else:
                self.enable_filter = 'Current Balance'

            if self.date_to_cmp:
                self.label_filter = self.date_to_cmp.strftime("%B %Y")
            else:
                self.enable_filter = 'Balance Periode'

        if self.enable_budget:
            self.label_balance = self.date_to.strftime("%B %Y")
            self.date_from_cmp = fields.Date.from_string(self.date_from) - relativedelta(years=1)
            self.date_to_cmp = fields.Date.from_string(self.date_to) - relativedelta(years=1)
            self.enable_budget_month = True
            self.enable_budget_year = True