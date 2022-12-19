# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Wilayah a+',
    'Author': 'Achmad T. Zaini',
    'Company' : 'Akunt+',
    'version': '1.1',
    'category': 'Wilayah',
    'summary': 'Wilayah',
    'description': """
        This module contains all the common features of Caroserie Pre-Sales Management.
    """,
    'depends': [
        "base",
        ],
    'data': [
        'security/wilayah_security.xml',
        'security/ir.model.access.csv',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False
}
