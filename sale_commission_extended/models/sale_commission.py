from odoo import api, fields, models, _


class SaleCommission(models.Model):
    _inherit = 'sale.commission'

    SALE_COMM = [
        ('fix', 'Fix Amount'),
        ('pct', 'Percentage'),
        ('section', 'By Sections')
    ]

    commission_type = fields.Selection(SALE_COMM, 'Type', required=True, default='fix')
    fix_qty = fields.Float(string='Rate')
    uom_ids = fields.Many2many(comodel_name='uom.uom', string='Unit of Measure')

    @api.onchange('commission_type')
    def onchange_comm_type(self):
        if self.commission_type != 'fix':
            self.uom_ids = None


class SaleCommissionMixin(models.AbstractModel):
    _inherit = 'sale.commission.mixin'

    product_categ_comm_ids = fields.One2many(comodel_name="sale.commission.line.mixin", inverse_name="object_id", copy=True)

    @api.model
    def _prepare_agents_vals_partner(self, partner):
        return []
        # rec = []
        # for p in partner.partner_categ_comm_ids:
        #     rec.append((0, 0, {
        #         'agent': p.agent_id.id,
        #         'commission': p.commission_id.id,
        #     }))
        # return rec

    @api.depends('commission_free', 'agents', 'product_categ_comm_ids')
    def _compute_commission_status(self, agent_id=None):
        pass
        # for line in self:
        #     partner_agents = [p.agent.id for p in line.agents]
        #     for p in line.product_categ_comm_ids:
        #         if p.agent.id not in partner_agents:
        #             partner_agents.append(p.agent.id)

        #     if line.commission_free:
        #         line.commission_status = _("Comm. free")
        #     elif len(partner_agents) == 0:
        #         line.commission_status = _("No commission agents")
        #     else:
        #         line.commission_status = _("%s commission agents") % len(partner_agents)


class SaleCommissionLineMixin(models.AbstractModel):
    _inherit = 'sale.commission.line.mixin'

    categ_id = fields.Many2one('product.category', 'Category')
    qty = fields.Float('Quantity')

    def _get_commission_amount(self, commission, subtotal, product, quantity):
        """Get the commission amount for the data given. To be called by
        compute methods of children models.
        """
        self.ensure_one()
        if product.commission_free or not commission:
            return 0.0
        if commission.amount_base_type == 'net_amount':
            # If subtotal (sale_price * quantity) is less than
            # standard_price * quantity, it means that we are selling at
            # lower price than we bought, so set amount_base to 0
            subtotal = max([0, subtotal - product.standard_price * quantity])

        if commission.commission_type == 'fix':
            return commission.fix_qty * quantity
        elif commission.commission_type == 'pct':
            return subtotal * (commission.fix_qty / 100.0)
        elif commission.commission_type == 'section':
            return commission.calculate_section(subtotal)
