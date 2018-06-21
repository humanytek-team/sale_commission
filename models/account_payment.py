from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    association_date = fields.Date(
        default=fields.date.today(),
    )
