# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Level of Approval',
    'author': 'Achmad T. Zaini',
    'email' : 'achmadtz@gmail.com',
    'version': '1.1',
    'category': 'Level of Approval',
    'summary': 'Level of Approval',
    'description': """
        Modul Level of Approval
""",
    'depends': [
        "base",
        "account",
        "sale",
        "purchase",
        "purchase_request",
        ],
    'data': [
        'security/loa_security.xml',
        'security/ir.model.access.csv',
        'views/loa_views.xml',
        'views/purchase.xml',
        'views/sale.xml',
        'views/hr_expense.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False
}
