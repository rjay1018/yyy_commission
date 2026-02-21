from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    partner_categ_comm_ids = fields.One2many('partner.category.commission', 'partner_id')
    product_categ_comm_ids = fields.One2many('product.category.commission', 'partner_id')
    agent_partner_categ_ids = fields.One2many('partner.category.commission', 'agent_id')
    agent_product_categ_ids = fields.One2many('product.category.commission', 'agent_id')
    commission_type = fields.Selection(related='commission.commission_type', store=True)


class PartnerCategoryCommission(models.Model):
    _name = 'partner.category.commission'

    partner_id = fields.Many2one('res.partner', 'Customer', ondelete='cascade')
    agent_id = fields.Many2one('res.partner', 'Agent', required=True, ondelete='cascade')
    commission_id = fields.Many2one('sale.commission', 'Commission Type', required=True)

    @api.onchange('partner_id')
    def onchange_partner(self):
        self.commission_id = None
        ctx = dict(self._context)
        if 'partner_categ' in ctx:
            if ctx['comm_type'] != 'fix':
                self.commission_id = ctx['comm_id']
        elif 'product_categ' in ctx:
            if ctx['comm_type'] == 'fix':
                self.commission_id = ctx['comm_id']
        else:
            if self.partner_id.commission.commission_type != 'fix':
                self.commission_id = self.agent_id.commission

    @api.onchange('agent_id')
    def onchange_agent(self):
        self.commission_id = self.agent_id.commission

    @api.multi
    @api.constrains('partner_id', 'agent_id')
    def _check_duplicate_agent(self):
        for obj in self:
            args = [
                ('partner_id', '=', obj.partner_id.id),
                ('agent_id', '=', obj.agent_id.id)
            ]
            if len(obj.search(args)) > 1:
                raise ValidationError(_('Duplicate sales agent exists'))


class ProductCategoryCommission(models.Model):
    _inherit = 'partner.category.commission'
    _name = 'product.category.commission'

    categ_id = fields.Many2one('product.category', 'Category', required=True)

    @api.multi
    @api.constrains('partner_id', 'agent_id')
    def _check_duplicate_agent(self):
        for obj in self:
            if obj.categ_id:
                args = [
                    ('categ_id', '=', obj.categ_id.id),
                    ('partner_id', '=', obj.partner_id.id),
                    ('agent_id', '=', obj.agent_id.id)
                ]
                if len(obj.search(args)) > 1:
                    raise ValidationError(_('Duplicate product category for an agent exists'))
