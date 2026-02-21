from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    COMP = [
        ('partner_categ', 'Partner Category Only'),
        ('product_categ', 'Product Category Only'),
        ('both', 'Both Partner and Product')
    ]

    agent_id = fields.Many2one('res.partner', 'Sales Agent')
    computation = fields.Selection(COMP, default='both')

    @api.depends('order_line.agents.amount', 'order_line.product_categ_comm_ids.amount')
    def _compute_commission_total(self):
        for obj in self:
            total = 0.0
            for l in obj.order_line:
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


class SaleOrderLine(models.Model):
    _inherit = [
        "sale.order.line",
        "sale.commission.mixin",
    ]
    _name = "sale.order.line"

    categ_id = fields.Many2one('product.category', 'Category')
    agents = fields.One2many(string="Agents & commissions", comodel_name="sale.order.line.agent", compute='_compute_partner_categ_commission', store=True)
    product_categ_comm_ids = fields.One2many('sale.order.line.categ', 'object_id', compute='_compute_product_categ_commission', store=True)

    @api.onchange('categ_id')
    def onchange_category(self):
        domain = []
        if self.categ_id:
            domain =[('categ_id', '=', self.categ_id.id)]
        return {'domain': {'product_id': domain}}

    @api.multi
    @api.depends('categ_id', 'product_uom_qty')
    def _compute_partner_categ_commission(self):
        for obj in self:
            if obj.order_id.computation != 'product_categ':
                obj._get_agents_comms_per_category('partner')

    @api.multi
    @api.depends('categ_id', 'product_uom_qty', 'product_uom')
    def _compute_product_categ_commission(self):
        for obj in self:
            if obj.order_id.computation != 'partner_categ':
                obj._get_agents_comms_per_category('product')

    @api.multi
    def _get_agent_comms(self, categ=''):
        agents_comms = None
        if categ == 'partner':
            self.agents = None
            agents_comms = self.order_id.partner_id.partner_categ_comm_ids
            if self.order_id.agent_id:
                agents_comms = agents_comms.filtered(lambda c: c.agent_id.id == self.order_id.agent_id.id)
        else:
            self.product_categ_comm_ids = None
            agents_comms = self.order_id.partner_id.product_categ_comm_ids.filtered(lambda c: c.categ_id.id == self.categ_id.id)
            if self.order_id.agent_id:
                agents_comms = agents_comms.filtered(lambda c: c.agent_id.id == self.order_id.agent_id.id)
        return agents_comms

    @api.multi
    def _get_agents_comms_per_category(self, categ=''):
        for obj in self:
            agents_comms = obj._get_agent_comms(categ)
            for a in agents_comms:
                amount = 0
                subtotal = obj.price_subtotal

                if a.commission_id.amount_base_type == 'net_amount':
                    subtotal = max([0, obj.price_subtotal - obj.product_id.standard_price * obj.product_uom_qty])

                if a.commission_id.commission_type == 'fix':
                    amount = obj.product_uom_qty * a.commission_id.fix_qty
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
                    vals['qty'] = obj.product_uom_qty

                    # Check if UOM has commission
                    if a.commission_id.uom_ids.filtered(lambda u: u.id == obj.product_uom.id):
                        obj.product_categ_comm_ids = [(0, 0, vals)]

    @api.onchange('product_id')
    def onchange_product(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id:
            if self.product_id.categ_id.id != self.categ_id.id:
                self.categ_id = self.product_id.categ_id.id
        return res

    def _prepare_agents_vals(self, vals=None):
        res = super()._prepare_agents_vals(vals=vals)
        if self:
            partner = self.order_id.partner_id
        else:
            order = self.env['sale.order'].browse(vals['order_id'])
            partner = order.partner_id
        return res #+ self._prepare_agents_vals_partner(partner)


class SaleOrderLineCateg(models.Model):
    _inherit = "sale.commission.line.mixin"
    _name = "sale.order.line.categ"

    object_id = fields.Many2one(comodel_name="sale.order.line", ondelete='cascade')
