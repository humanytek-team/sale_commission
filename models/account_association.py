from odoo import fields,  models


class AccountAssociation(models.Model):
    _name = 'account.association'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        ondelete='cascade',
    )
    payment_id = fields.Many2one(
        comodel_name='account.payment',
        ondelete='cascade',
    )
    date = fields.Date(
    )
