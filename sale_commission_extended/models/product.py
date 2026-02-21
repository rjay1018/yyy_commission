
from odoo import fields, models, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    has_commission = fields.Boolean(default=True)

    def apply_commission_to_products(self):
        obj_product = self.env['product.template']
        products = obj_product.search([('categ_id', '=', self.id)])
        for p in products:
            if self.has_commission:
                p.commission_free = False
            else:
                p.commission_free = True
