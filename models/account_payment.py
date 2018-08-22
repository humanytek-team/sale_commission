from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    association_ids = fields.One2many(
        comodel_name='account.association',
        inverse_name='payment_id',
    )

    @api.multi
    def post(self):
        super(AccountPayment, self).post()
        try:
            invoice_ids = self.env['account.invoice'].browse(self._context.get('active_ids'))
            for invoice in invoice_ids:
                self.env['account.association'].create({
                    'invoice_id': invoice.id,
                    'payment_id': self.id,
                    'date': fields.Date.today(),
                })
        except Exception as e:
            pass
