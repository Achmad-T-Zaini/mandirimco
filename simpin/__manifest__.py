# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Simpan Pinjam',
    'author': 'Achmad T. Zaini',
    'email' : 'achmadtz@gmail.com',
    'version': '1.1',
    'category': 'Simpin',
    'summary': 'Simpan Pinjam',
    'description': """
        Modul Simpan Pinjam
""",
    'depends': [
#        "base_setup",
        "base",
        "account",
        "product",
#        "wilayah",
#        "sale",
#        "purchase",
#        "purchase_request",
#        "mail",
#        "portal"
        ],
    'data': [
        'security/simpin_security.xml',
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/member_views.xml',
        'views/config_views.xml',
        'views/product_template_view.xml',
        'views/pinjaman_views.xml',
        'views/investasi_views.xml',
        'report/jadwal_angsuran.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
