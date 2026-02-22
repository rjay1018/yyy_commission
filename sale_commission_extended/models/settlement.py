from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class SaleCommissionMakeSettle(models.TransientModel):
    _inherit = "sale.commission.make.settle"

    def _get_unsettled_invoices(self, inv_for, date_to_agent, agent_id):
        args = [
                ('invoice_date', '<', date_to_agent),
                ('agent', '=', agent_id),
                ('settled', '=', False)
            ]
        if inv_for == 'partner_categ':
            return self.env['account.invoice.line.agent'].search(args, order='invoice_date')
        else:
            return self.env['account.invoice.line.categ'].search(args, order='invoice_date')

    def _process_settlement(self, agent, agent_lines, inv_for):
        settlement_obj = self.env['sale.commission.settlement']
        settlement_line_obj = self.env['sale.commission.settlement.line']
        settlement_line_categ_obj = self.env['sale.commission.settlement.line.categ']
        settlement_ids = []

        for company in agent_lines.mapped('company_id'):
            agent_lines_company = agent_lines.filtered(lambda r: r.object_id.company_id == company)
            if not agent_lines_company:
                continue
            pos = 0
            sett_to = date(year=1900, month=1, day=1)
            while pos < len(agent_lines_company):
                line = agent_lines_company[pos]
                pos += 1
                if line._skip_settlement():
                    continue
                if line.invoice_date > sett_to:
                    sett_from = self._get_period_start(agent, line.invoice_date)
                    sett_to = self._get_next_period_date(agent, sett_from) - timedelta(days=1)
                    settlement = self._get_settlement(agent, company, sett_from, sett_to)
                    if not settlement:
                        settlement = settlement_obj.create(
                                self._prepare_settlement_vals(
                                    agent, company, sett_from, sett_to
                            )
                        )
                    settlement_ids.append(settlement.id)

                vals = {'settlement': settlement.id}
                if inv_for == 'partner_categ':
                    vals['agent_line'] = [(6, 0, [line.id])]
                    settlement_line_obj.create(vals)
                else:
                    vals['agent_line_categ'] = [(6, 0, [line.id])]
                    settlement_line_categ_obj.create(vals)
        return settlement_ids

    @api.multi
    def action_settle(self):
        self.ensure_one()
        settlement_ids = []
        if not self.agents:
            self.agents = self.env['res.partner'].search([('agent', '=', True)])
        date_to = self.date_to
        for agent in self.agents:
            date_to_agent = self._get_period_start(agent, date_to)

            # Partner Category
            settlement_ids.extend(self._process_settlement(
                        agent,
                        self._get_unsettled_invoices('partner_categ', date_to_agent, agent.id),
                        'partner_categ'
                    )
                )

            # Product Category
            settlement_ids.extend(self._process_settlement(
                        agent,
                        self._get_unsettled_invoices('product_categ', date_to_agent, agent.id),
                        'product_categ'
                    )
                )

        if len(settlement_ids):
            return {
                'name': _('Created Settlements'),
                'type': 'ir.actions.act_window',
                'views': [[False, 'list'], [False, 'form']],
                'res_model': 'sale.commission.settlement',
                'domain': [['id', 'in', settlement_ids]],
            }
        else: return {'type': 'ir.actions.act_window_close'}



class Settlement(models.Model):
    _inherit = "sale.commission.settlement"

    categ_lines = fields.One2many(comodel_name="sale.commission.settlement.line.categ", inverse_name="settlement", readonly=True)

    @api.depends('lines', 'lines.settled_amount', 'categ_lines', 'categ_lines.settled_amount')
    def _compute_total(self):
        for record in self:
            record.total = sum(x.settled_amount for x in record.lines) + sum(x.settled_amount for x in record.categ_lines)

    @api.multi
    def button_recompute_lines(self):
        """Recompute commission amounts on all settlement lines."""
        for settlement in self:
            if settlement.state != 'settled':
                raise ValidationError(_("Only settlements in 'Settled' state can be recomputed."))
            settlement._recompute_settlement_lines()
            
        return True

    @api.multi
    def _recompute_settlement_lines(self):
        """Recalculate commission amounts on the underlying agent lines
        by triggering their compute methods.
        """
        self.ensure_one()

        # Recompute partner category lines (sale.commission.settlement.line)
        for sline in self.lines:
            if sline.agent_line:
                sline.agent_line._compute_amount()

        # Recompute product category lines (sale.commission.settlement.line.categ)
        for sline in self.categ_lines:
            if sline.agent_line_categ:
                sline.agent_line_categ._compute_amount()


class SettlementLineCateg(models.Model):
    _name = "sale.commission.settlement.line.categ"

    settlement = fields.Many2one("sale.commission.settlement", readonly=True, ondelete="cascade", required=True)
    agent_line_categ = fields.Many2many(
        comodel_name='account.invoice.line.categ',
        relation='settlement_agent_line_categ_rel', column1='settlement_id',
        column2='agent_line_categ_id', required=True)
    date = fields.Date(related="agent_line_categ.invoice_date", store=True)
    invoice_line = fields.Many2one(
        comodel_name='account.invoice.line', store=True,
        related='agent_line_categ.object_id')
    invoice = fields.Many2one(
        comodel_name='account.invoice', store=True, string="Invoice",
        related='invoice_line.invoice_id')
    agent = fields.Many2one(
        comodel_name="res.partner", readonly=True, related="agent_line_categ.agent",
        store=True)
    settled_amount = fields.Monetary(
        related="agent_line_categ.amount", readonly=True, store=True)
    currency_id = fields.Many2one(
        related="agent_line_categ.currency_id",
        store=True,
        readonly=True,
    )
    commission = fields.Many2one(
        comodel_name="sale.commission", related="agent_line_categ.commission")
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='settlement.company_id',
    )

    @api.constrains('settlement', 'agent_line_categ')
    def _check_company(self):
        for record in self:
            for line in record.agent_line_categ:
                if line.company_id != record.company_id:
                    raise UserError(_("Company must be the same"))
