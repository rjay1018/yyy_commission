from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    COMP = [
        ('partner_categ', 'Partner Category Only'),
        ('product_categ', 'Product Category Only'),
        ('both', 'Both Partner and Product')
    ]

    agent_id = fields.Many2one('res.partner', 'Sales Agent')
    computation = fields.Selection(COMP, default='both')

    @api.depends('invoice_line_ids.agents.amount', 'invoice_line_ids.product_categ_comm_ids.amount')
    def _compute_commission_total(self):
        for obj in self:
            total = 0.0
            for l in obj.invoice_line_ids:
                total += sum(x.amount for x in l.agents)
                total += sum(x.amount for x in l.product_categ_comm_ids)
            obj.commission_total = total

    @api.onchange('partner_id')
    def onchange_partner(self):
        self.agent_id = None
        agent_ids = []
        domain = [('agent', '!=', False)]
        if self.partner_id:
            for p in self.partner_id.partner_categ_comm_ids:
                if p.agent_id.id not in agent_ids:
                    agent_ids.append(p.agent_id.id)
            for p in self.partner_id.product_categ_comm_ids:
                if p.agent_id.id not in agent_ids:
                    agent_ids.append(p.agent_id.id)

        if agent_ids:
            domain.extend([('id', 'in', agent_ids)])
        return {'domain': {'agent_id': domain}}


class AccountInvoiceLine(models.Model):
    _inherit = [
        "account.invoice.line",
        "sale.commission.mixin",
    ]
    _name = "account.invoice.line"

    categ_id = fields.Many2one('product.category', 'Category')
    # product_categ_comm_ids = fields.One2many('account.invoice.line.categ', 'object_id', compute='_compute_categ_commission', store=True)
    agents = fields.One2many(string="Agents & commissions", comodel_name="account.invoice.line.agent", compute='_compute_partner_categ_commission', store=True)
    product_categ_comm_ids = fields.One2many('account.invoice.line.categ', 'object_id', compute='_compute_product_categ_commission', store=True)

    @api.model
    def create(self, vals):
        """Add agents for records created from automations instead of UI."""
        # We use this form as this is the way it's returned when no real vals
        agents_vals = vals.get('agents', [(6, 0, [])])
        invoice_id = vals.get('invoice_id', False)        
        if (agents_vals and agents_vals[0][0] == 6 and not
                agents_vals[0][2] and invoice_id):
            vals['agents'] = self._prepare_agents_vals(vals=vals)
        res = super().create(vals)
        for r in res:
            for sol in r.sale_line_ids:
                r.invoice_id.agent_id = sol.order_id.agent_id.id
                r.invoice_id.computation = sol.order_id.computation
                r.categ_id = sol.categ_id.id
        return res

    @api.onchange('product_id')
    def onchange_product(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        if self.product_id:
            if self.product_id.categ_id.id != self.categ_id.id:
                self.categ_id = self.product_id.categ_id.id
        return res

    @api.onchange('categ_id')
    def onchange_category(self):
        domain = []
        if self.categ_id:
            domain =[('categ_id', '=', self.categ_id.id)]
        return {'domain': {'product_id': domain}}

    @api.multi
    @api.depends('categ_id', 'quantity')
    def _compute_partner_categ_commission(self):
        for obj in self:
            if obj.invoice_id.computation != 'product_categ':
                obj._get_agents_comms_per_category('partner')

    @api.multi
    @api.depends('categ_id', 'quantity', 'uom_id')
    def _compute_product_categ_commission(self):
        for obj in self:
            if obj.invoice_id.computation != 'partner_categ':
                obj._get_agents_comms_per_category('product')

    @api.multi
    def _get_agent_comms(self, categ=''):
        agents_comms = None
        if categ == 'partner':
            self.agents = None
            agents_comms = self.invoice_id.partner_id.partner_categ_comm_ids
            if self.invoice_id.agent_id:
                agents_comms = agents_comms.filtered(lambda c: c.agent_id.id == self.invoice_id.agent_id.id)
        else:
            self.product_categ_comm_ids = None
            agents_comms = self.invoice_id.partner_id.product_categ_comm_ids.filtered(lambda c: c.categ_id.id == self.categ_id.id)
            if self.invoice_id.agent_id:
                agents_comms = agents_comms.filtered(lambda c: c.agent_id.id == self.invoice_id.agent_id.id)
        return agents_comms

    @api.multi
    def _get_agents_comms_per_category(self, categ=''):
        for obj in self:
            if getattr(obj, 'display_type', False) in ('line_note', 'line_section'):
                continue
            agents_comms = obj._get_agent_comms(categ)
            for a in agents_comms:
                amount = 0
                subtotal = obj.price_subtotal

                if a.commission_id.amount_base_type == 'net_amount':
                    subtotal = max([0, obj.price_subtotal - obj.product_id.standard_price * obj.quantity])

                if a.commission_id.commission_type == 'fix':
                    amount = obj.quantity * a.commission_id.fix_qty
                elif a.commission_id.commission_type == 'pct':
                    amount = subtotal * (a.commission_id.fix_qty / 100.0)
                else:
                    for s in a.commission_id.sections:
                        if s.amount_from <= subtotal <= s.amount_to:
                            amount = subtotal * (s.percent / 100.0)

                vals = {
                    'agent': a.agent_id.id,
                    'commission': a.commission_id.id,
                    'amount': amount
                }
                if categ == 'partner':
                    obj.agents = [(0, 0, vals)]
                else:
                    vals['categ_id'] = obj.categ_id.id
                    vals['qty'] = obj.quantity

                    # Check if UOM has commission
                    if a.commission_id.uom_ids.filtered(lambda u: u.id == obj.uom_id.id):
                        obj.product_categ_comm_ids = [(0, 0, vals)]

    # @api.depends('categ_id', 'quantity')
    # def _compute_categ_commission(self):
    #     self._get_agents_comm_per_category()

    # @api.multi
    # def _get_agents_comm_per_category(self):
    #     for obj in self:
    #         obj.product_categ_comm_ids = None
    #         agents_comms = obj.invoice_id.partner_id.product_categ_comm_ids.filtered(lambda c: c.categ_id.id == obj.categ_id.id)
    #         for a in agents_comms:
    #             amount = 0
    #             subtotal = obj.price_subtotal

    #             if a.commission_id.amount_base_type == 'net_amount':
    #                 subtotal = max([0, obj.price_subtotal - obj.product_id.standard_price * obj.quantity])

    #             if a.commission_id.commission_type == 'fix':
    #                 amount = obj.quantity * a.commission_id.fix_qty
    #             elif a.commission_id.commission_type == 'pct':
    #                 amount = subtotal * (a.commission_id.fix_qty / 100.0)
    #             else:
    #                 for s in a.commission_id.sections:
    #                     if s.amount_from <= subtotal <= s.amount_to:
    #                         amount = subtotal * (s.percent / 100.0)

    #             vals = {
    #                 # 'object_id': obj.id,
    #                 'categ_id': obj.categ_id.id,
    #                 'qty': obj.quantity,
    #                 'agent': a.agent_id.id,
    #                 'commission': a.commission_id.id,
    #                 'amount': amount
    #             }
    #             obj.product_categ_comm_ids = [(0, 0, vals)]


class AccountInvoiceLineAgent(models.Model):
    _inherit = "account.invoice.line.agent"

    @api.constrains('agent', 'amount')
    def _check_settle_integrity(self):
        for record in self:
            if any(x.settlement.state == 'invoiced' for x in record.agent_line):
                raise ValidationError(
                    _("You can't modify an invoiced commission line"),
                )

    def _skip_settlement(self):
        res = super(AccountInvoiceLineAgent, self)._skip_settlement()
        if getattr(self.object_id, 'display_type', False) in ('line_note', 'line_section'):
            return True
        return res


class AccountInvoiceLineCateg(models.Model):
    _inherit = "sale.commission.line.mixin"
    _name = "account.invoice.line.categ"

    object_id = fields.Many2one(
        comodel_name="account.invoice.line",
        oldname='invoice_line',
    )
    invoice = fields.Many2one(
        string="Invoice",
        comodel_name="account.invoice",
        related="object_id.invoice_id",
        store=True,
    )
    invoice_date = fields.Date(
        string="Invoice date",
        related="invoice.date_invoice",
        store=True,
        readonly=True,
    )
    # agent_line = fields.Many2many(
    #     comodel_name='sale.commission.settlement.line',
    #     relation='settlement_agent_line_categ_rel',
    #     column1='agent_line_id',
    #     column2='settlement_id',
    #     copy=False,
    # )
    agent_line_categ = fields.Many2many(
        comodel_name='sale.commission.settlement.line.categ',
        relation='settlement_agent_line_categ_rel',
        column1='agent_line_categ_id',
        column2='settlement_id',
        copy=False,
    )
    settled = fields.Boolean(
        compute="_compute_settled",
        store=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        compute="_compute_company",
        store=True,
    )
    currency_id = fields.Many2one(
        related="object_id.currency_id",
        readonly=True,
    )

    @api.depends('object_id.price_subtotal')
    def _compute_amount(self):
        for line in self:
            inv_line = line.object_id
            line.amount = line._get_commission_amount(
                line.commission, inv_line.price_subtotal,
                inv_line.product_id, inv_line.quantity,
            )
            # Refunds commissions are negative
            if 'refund' in line.invoice.type:
                line.amount = -line.amount

    @api.depends('agent_line_categ', 'agent_line_categ.settlement.state', 'invoice', 'invoice.state')
    def _compute_settled(self):
        # Count lines of not open or paid invoices as settled for not
        # being included in settlements
        for line in self:
            line.settled = (any(x.settlement.state != 'cancel' for x in line.agent_line_categ))

    @api.depends('object_id', 'object_id.company_id')
    def _compute_company(self):
        for line in self:
            line.company_id = line.object_id.company_id

    @api.constrains('agent', 'amount')
    def _check_settle_integrity(self):
        for record in self:
            if any(x.settlement.state == 'invoiced' for x in record.agent_line_categ):
                raise ValidationError(
                    _("You can't modify an invoiced commission line"),
                )

    def _skip_settlement(self):
        """This function should return if the commission can be payed.

        :return: bool
        """
        self.ensure_one()
        skip = (
            self.commission.invoice_state == 'paid' and
            self.invoice.state != 'paid'
        ) or (self.invoice.state not in ('open', 'paid'))
        
        if not skip and getattr(self.object_id, 'display_type', False) in ('line_note', 'line_section'):
            skip = True
            
        return skip
