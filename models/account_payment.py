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
            invoice_id = self.env['account.invoice'].browse(self._context.get('active_id'))
            self.env['account.association'].create({
                'invoice_id': invoice_id.id,
                'payment_id': self.id,
                'date': fields.Date.today(),
            })
        except Exception as e:
            pass
