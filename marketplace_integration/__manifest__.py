# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MarketPlace Integration',
    'author': 'Achmad T. Zaini',
    'email' : 'achmadtz@gmail.com',
    'version': '14.1',
    'category': 'MarketPlace Integration',
    'summary': 'MarketPlace Integration',
    'description': """
        Modul MarketPlace Integration
""",
    'depends': [
        "base",
        "account",
        "sale",
        ],
    'data': [
        'security/marketplace_security.xml',
        'security/ir.model.access.csv',
        'views/marketplace_views.xml',
#        'views/sale.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
