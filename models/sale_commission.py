# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2017 Humanytek (<www.humanytek.com>).
#    Rubén Bravo <rubenred18@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import api, fields, models
import datetime
import logging
_logger = logging.getLogger(__name__)


class SaleCommission(models.TransientModel):
    _name = "sale.commission"

    @api.multi
    def calculate(self):
        AccountInvoice = self.env['account.invoice']
        SaleCommissionDetail = self.env['sale.commission.detail']
        SaleCommissionBrand = self.env['sale.commission.brand']
        SaleCommissionSetting = self.env['sale.commission.setting']

        sale_commission_setting = SaleCommissionSetting.search([], limit=1)
        commi = 0
        sett_day = 0
        if sale_commission_setting:
            commi = sale_commission_setting.commission / 100
            sett_day = sale_commission_setting.day
        domain = []
        if self.user_id:
            domain = [
                        ('user_id', '=', self.user_id.id),
                        ('payment_move_line_ids', '!=', False)]
        else:
            domain = [
                        ('user_id', '=', False),
                        ('payment_move_line_ids', '!=', False)]
        account_invoices = AccountInvoice.search(domain)
        #account_invoices = AccountInvoice.search([
                                #('user_id', '=', self.user_id.id),
                                ##('date_invoice', '>=', self.date_start),
                                ##('date_invoice', '<=', self.date_end),
                                #('payment_move_line_ids', '!=', False)])
        SaleCommissionDetail.search([]).unlink()

        for account_invoice in account_invoices:
            inte = 0
            if account_invoice.invoice_line_ids[0].product_id.product_brand_id:
                sale_commission_brand = SaleCommissionBrand.search([
                    ('user_id', '=', account_invoice.user_id.id),
                    ('brand_id', '=', account_invoice.invoice_line_ids[0].product_id.product_brand_id.id)],
                    limit=1)
                if sale_commission_brand:
                    inte = sale_commission_brand[0].commission / 100
            #for payment in account_invoice.payment_ids:
            for payment in account_invoice.payment_move_line_ids:
                payment_currency_id = False
                amount = sum([p.amount for p in payment.matched_debit_ids if p.debit_move_id in account_invoice.move_id.line_ids])
                amount_currency = sum([p.amount_currency for p in payment.matched_debit_ids if p.debit_move_id in account_invoice.move_id.line_ids])
                if payment.matched_debit_ids:
                    payment_currency_id = all([p.currency_id == payment.matched_debit_ids[0].currency_id for p in payment.matched_debit_ids]) and payment.matched_debit_ids[0].currency_id or False
                if payment_currency_id and payment_currency_id == account_invoice.currency_id:
                    amount_to_show = amount_currency
                else:
                    amount_to_show = payment.company_id.currency_id.with_context(date=payment.date).compute(amount, account_invoice.currency_id)
                amount = amount_to_show
                if payment.payment_id.payment_date and account_invoice.date_due:
                    if payment.payment_id.payment_date >= self.date_start and payment.payment_id.payment_date <= self.date_end:
                        day_difference = datetime.datetime.strptime(payment.payment_id.payment_date, "%Y-%m-%d") - datetime.datetime.strptime(account_invoice.date_due, "%Y-%m-%d")
                        day = 0
                        if day_difference.days > sett_day:
                            day = int(day_difference.days)
                        penalization = ((amount * commi) / 30) * day
                        before_penalization = amount * inte
                        commission = before_penalization - penalization
                        SaleCommissionDetail.create({
                            'account_payment_amount': amount,
                            'sale_commission_id': self.id,
                            'account_invoice_id': account_invoice.id,
                            'account_payment_id': payment.payment_id.id,
                            'day_difference': day_difference.days,
                            'day_int': day,
                            'penalization': penalization,
                            'commission_brand': inte,
                            'before_penalization': before_penalization,
                            'commission': commission
                            })

        return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.commission',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
                }

    user_id = fields.Many2one('res.users', 'Salesman')
    date_start = fields.Datetime('Start Date',
                                    required=True)
    date_end = fields.Datetime('End Date',
                                    required=True)
    sale_commission_detail_ids = fields.One2many('sale.commission.detail',
                            'sale_commission_id',
                            'Detail')
    commission_tax = fields.Float('Commission with tax',
                                compute='_compute_commission',
                                readonly=True)
    commission = fields.Float('Commission',
                                compute='_compute_commission',
                                readonly=True)

    @api.multi
    def print_commission(self):
        Report = self.env['report']
        return Report.get_action(
            self,
            'sale_commission.sale_commission_report2')

    @api.multi
    def _compute_commission(self):
        self.commission_tax = sum([sale_commission_detail.commission
                                for sale_commission_detail in
                                self.sale_commission_detail_ids
                                #if product_compromise.state == 'assigned'
                                ])
        self.commission = (self.commission_tax -
                            (self.commission_tax * 0.16))


class SaleCommissionDetail(models.TransientModel):
    _name = "sale.commission.detail"

    sale_commission_id = fields.Many2one('sale.commission', 'Commission')
    account_invoice_id = fields.Many2one('account.invoice', 'Invoice',
                                        readonly=True)
    account_invoice_number = fields.Char(related='account_invoice_id.number',
                            string='Number', readonly=True, store=False)
    account_invoice_date = fields.Date(
                            related='account_invoice_id.date_due',
                            string='Invoice Date', readonly=True, store=False)
    partner_id = fields.Many2one(related='account_invoice_id.partner_id',
                            string='Customer',
                            readonly=True, store=False)
    currency_id = fields.Many2one(related='account_invoice_id.currency_id',
                            string='Currency',
                            readonly=True, store=False)
    account_payment_id = fields.Many2one('account.payment', 'Payment',
                                        readonly=True)
    account_payment_date = fields.Date(
                            related='account_payment_id.payment_date',
                            string='Payment Date', readonly=True, store=False)
    account_payment_amount = fields.Monetary(
                            string='Amount', readonly=True)
    day_difference = fields.Integer('Difference Days')
    day_int = fields.Integer('Int. Days')
    penalization = fields.Float('Penalization Amount')
    before_penalization = fields.Float('Before Penalization Amount')
    commission = fields.Float('Commission')
    commission_brand = fields.Float('Commission Brand', (2, 4))


class SaleCommissionBrand(models.Model):
    _name = "sale.commission.brand"

    user_id = fields.Many2one('res.users', 'Salesman', required=True)
    brand_id = fields.Many2one('product.brand', 'Brand', required=True)
    commission = fields.Float('Commission (%)', required=True)


class SaleCommissionSetting(models.Model):
    _name = "sale.commission.setting"

    day = fields.Integer('Days', required=True)
    commission = fields.Float('Commission (%)', (2, 4), required=True)
