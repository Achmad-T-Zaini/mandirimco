# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Petty Cash',
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Petty Cash',
    'author': 'Achmad T. Zaini, ',
    'depends': ['account', 'base',
                'level_of_approval',
                ],
    'data': [
        'security/petty_cash_security.xml',
        'security/ir.model.access.csv',
        'views/petty_cash_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
