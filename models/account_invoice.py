from odoo import api, fields,  models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    association_ids = fields.One2many(
        comodel_name='account.association',
        inverse_name='invoice_id',
    )

    @api.multi
    def assign_outstanding_credit(self, credit_aml_id):
        r = super(AccountInvoice, self).assign_outstanding_credit(credit_aml_id)
        credit_aml = self.env['account.move.line'].browse(credit_aml_id)
        if credit_aml.payment_id:
            self.env['account.association'].create({
                'invoice_id': self.id,
                'payment_id': credit_aml.payment_id.id,
                'date': fields.Date.today(),
            })
        return r
