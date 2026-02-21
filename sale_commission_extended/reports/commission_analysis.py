from odoo import models, fields, api, tools, _
from psycopg2.extensions import AsIs


class SaleOrderCommissionAnalysisReport(models.Model):
    _inherit = "sale.order.commission.analysis.report"

    def _select_sub_qry(self):
        select_str = '''
            SELECT ROW_NUMBER() OVER (ORDER BY sub.partner_id) AS id,
                sub.partner_id,
                sub.order_state,
                sub.date_order,
                sub.company_id,
                sub.salesman_id,
                sub.agent_id,
                sub.categ_id,
                sub.product_id,
                sub.uom_id,
                AVG(sub.quantity) AS quantity,
                AVG(sub.price_unit) AS price_unit,
                AVG(sub.price_subtotal) AS price_subtotal,
                AVG(sub.percentage) AS percentage,
                AVG(sub.amount) AS amount,
                sub.order_line_id,
                sub.commission_id
            FROM
            '''
        return select_str

    def _select_qry(self):
        select_str = '''
            ((SELECT so.partner_id AS partner_id,
                so.state AS order_state,
                so.date_order AS date_order,
                sol.company_id AS company_id,
                sol.salesman_id AS salesman_id,
                rp.id AS agent_id,
                pt.categ_id AS categ_id,
                sol.product_id AS product_id,
                pt.uom_id AS uom_id,
                SUM(sol.product_uom_qty) AS quantity,
                AVG(sol.price_unit) AS price_unit,
                SUM(sol.price_subtotal) AS price_subtotal,
                AVG(sc.fix_qty) AS percentage,
                SUM(sola.amount) AS amount,
                sol.id AS order_line_id,
                sola.commission AS commission_id
            FROM sale_order_line_agent sola
                LEFT JOIN sale_order_line sol ON sol.id = sola.object_id
                INNER JOIN sale_order so ON so.id = sol.order_id
                LEFT JOIN sale_commission sc ON sc.id = sola.commission
                LEFT JOIN product_product pp ON pp.id = sol.product_id
                INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN res_partner rp ON sola.agent = rp.id
            GROUP BY so.partner_id,
                so.state,
                so.date_order,
                sol.company_id,
                sol.salesman_id,
                rp.id,
                pt.categ_id,
                sol.product_id,
                pt.uom_id,
                sol.id,
                sola.commission)

            UNION ALL

            (SELECT 
                so.partner_id AS partner_id,
                so.state AS order_state,
                so.date_order AS date_order,
                sol.company_id AS company_id,
                sol.salesman_id AS salesman_id,
                rp.id AS agent_id,
                pt.categ_id AS categ_id,
                sol.product_id AS product_id,
                pt.uom_id AS uom_id,
                SUM(sol.product_uom_qty) AS quantity,
                AVG(sol.price_unit) AS price_unit,
                SUM(sol.price_subtotal) AS price_subtotal,
                AVG(sc.fix_qty) AS percentage,
                SUM(sola.amount) AS amount,
                sol.id AS order_line_id,
                sola.commission AS commission_id
            FROM sale_order_line_agent sola
                LEFT JOIN sale_order_line sol ON sol.id = sola.object_id
                INNER JOIN sale_order so ON so.id = sol.order_id
                LEFT JOIN sale_commission sc ON sc.id = sola.commission
                LEFT JOIN product_product pp ON pp.id = sol.product_id
                INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN res_partner rp ON sola.agent = rp.id
            GROUP BY so.partner_id,
                so.state,
                so.date_order,
                sol.company_id,
                sol.salesman_id,
                rp.id,
                pt.categ_id,
                sol.product_id,
                pt.uom_id,
                sol.id,
                sola.commission)) AS sub
            GROUP BY 
                sub.partner_id,
                sub.order_state,
                sub.date_order,
                sub.company_id,
                sub.salesman_id,
                sub.agent_id,
                sub.categ_id,
                sub.product_id,
                sub.uom_id,
                sub.order_line_id,
                sub.commission_id
            '''
        return select_str

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            "CREATE or REPLACE VIEW %s AS ( %s%s )", (
                AsIs(self._table),
                AsIs(self._select_sub_qry()),
                AsIs(self._select_qry())
            ),
        )


class SaleCommissionAnalysisReport(models.Model):
    _inherit = "sale.commission.analysis.report"

    def _select_sub_qry(self):
        select_str = '''
            SELECT ROW_NUMBER() OVER (ORDER BY sub.partner_id) AS id,
                sub.partner_id,
                sub.invoice_state,
                sub.date_invoice,
                sub.company_id,
                sub.agent_id,
                sub.categ_id,
                sub.product_id,
                sub.uom_id,
                AVG(sub.quantity) AS quantity,
                AVG(sub.price_unit) AS price_unit,
                AVG(sub.price_subtotal) AS price_subtotal,
                AVG(sub.price_subtotal_signed) AS price_subtotal_signed,
                AVG(sub.percentage) AS percentage,
                AVG(sub.amount) AS amount,
                sub.invoice_line_id,
                sub.settled,
                sub.commission_id
            FROM
            '''
        return select_str

    def _select_qry(self):
        select_str = '''
            ((SELECT ai.partner_id AS partner_id,
                ai.state AS invoice_state,
                ai.date_invoice AS date_invoice,
                ail.company_id AS company_id,
                rp.id AS agent_id,
                pt.categ_id AS categ_id,
                ail.product_id AS product_id,
                pt.uom_id AS uom_id,
                SUM(ail.quantity) AS quantity,
                AVG(ail.price_unit) AS price_unit,
                SUM(ail.price_subtotal) AS price_subtotal,
                SUM(ail.price_subtotal_signed) AS price_subtotal_signed,
                AVG(sc.fix_qty) AS percentage,
                SUM(aila.amount) AS amount,
                ail.id AS invoice_line_id,
                aila.settled AS settled,
                aila.commission AS commission_id
            FROM account_invoice_line_agent aila
                LEFT JOIN account_invoice_line ail ON ail.id = aila.object_id
                INNER JOIN account_invoice ai ON ai.id = ail.invoice_id
                LEFT JOIN sale_commission sc ON sc.id = aila.commission
                LEFT JOIN product_product pp ON pp.id = ail.product_id
                INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN res_partner rp ON aila.agent = rp.id 
            GROUP BY ai.partner_id,
                ai.state,
                ai.date_invoice,
                ail.company_id,
                rp.id,
                pt.categ_id,
                ail.product_id,
                pt.uom_id,
                ail.id,
                aila.settled,
                aila.commission)
                
            UNION ALL

            (SELECT ai.partner_id AS partner_id,
                ai.state AS invoice_state,
                ai.date_invoice AS date_invoice,
                ail.company_id AS company_id,
                rp.id AS agent_id,
                pt.categ_id AS categ_id,
                ail.product_id AS product_id,
                pt.uom_id AS uom_id,
                SUM(ail.quantity) AS quantity,
                AVG(ail.price_unit) AS price_unit,
                SUM(ail.price_subtotal) AS price_subtotal,
                SUM(ail.price_subtotal_signed) AS price_subtotal_signed,
                AVG(sc.fix_qty) AS percentage,
                SUM(ailc.amount) AS amount,
                ail.id AS invoice_line_id,
                ailc.settled AS settled,
                ailc.commission AS commission_id
            FROM account_invoice_line_categ ailc
                LEFT JOIN account_invoice_line ail ON ail.id = ailc.object_id
                INNER JOIN account_invoice ai ON ai.id = ail.invoice_id
                LEFT JOIN sale_commission sc ON sc.id = ailc.commission
                LEFT JOIN product_product pp ON pp.id = ail.product_id
                INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN res_partner rp ON ailc.agent = rp.id 
            GROUP BY ai.partner_id,
                ai.state,
                ai.date_invoice,
                ail.company_id,
                rp.id,
                pt.categ_id,
                ail.product_id,
                pt.uom_id,
                ail.id,
                ailc.settled,
                ailc.commission)) AS sub
            GROUP BY sub.partner_id,
                sub.invoice_state,
                sub.date_invoice,
                sub.company_id,
                sub.agent_id,
                sub.categ_id,
                sub.product_id,
                sub.uom_id,
                sub.invoice_line_id,
                sub.settled,
                sub.commission_id
                    '''
        return select_str

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            "CREATE or REPLACE VIEW %s AS ( %s%s )", (
                AsIs(self._table),
                AsIs(self._select_sub_qry()),
                AsIs(self._select_qry())
            ),
        )