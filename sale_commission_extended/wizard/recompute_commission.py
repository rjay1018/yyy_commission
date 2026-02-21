from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class SaleCommissionRecompute(models.TransientModel):
    _name = 'sale.commission.recompute'
    _description = 'Recompute Commissions on Invoices'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    agent_id = fields.Many2one('res.partner', string='Sales Agent',
                               domain=[('agent', '=', True)])
    invoice_state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
    ], string='Invoice State')

    @api.multi
    def action_recompute(self):
        self.ensure_one()
        invoices = self._get_invoices()
        count = self._recompute_invoices(invoices)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recompute Commissions'),
                'message': _('%d invoice(s) recomputed successfully.') % count,
                'sticky': False,
            }
        }

    def _get_invoices(self):
        """Search for invoices matching the wizard filters."""
        domain = [('type', 'in', ['out_invoice', 'out_refund'])]

        if self.date_from:
            domain.append(('date_invoice', '>=', self.date_from))
        if self.date_to:
            domain.append(('date_invoice', '<=', self.date_to))
        if self.invoice_state:
            domain.append(('state', '=', self.invoice_state))
        if self.agent_id:
            domain.append(('agent_id', '=', self.agent_id.id))

        return self.env['account.invoice'].search(domain)

    def _recompute_invoices(self, invoices):
        """Recompute commission lines for the given invoices."""
        count = 0
        for invoice in invoices:
            invoice._recompute_commissions()
            count += 1
        return count
