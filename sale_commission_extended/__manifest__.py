{
    'name': 'Sales Commissions - Extended',
    'version': '12.0.2',
    'author': 'Allan J. Manuel',
    'category': 'Sales Management',
    'license': 'AGPL-3',
    'depends': ['sale_commission'],
    'website': 'https://github.com/OCA/commission',
    'data': [
        'security/ir.model.access.csv',
        'views/product.xml',
        'views/partner.xml',
        'views/sale_commission.xml',
        'views/sale_order.xml',
        'views/account_invoice.xml',
        'views/settlement.xml',
        'reports/commission_analysis.xml',
        'reports/settlement_report.xml'
    ],
    'installable': True
}
