# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Mandiri API',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Mandiri API',
    'author': 'Achmad T. Zaini, ',
    'depends': [
                'account',
                ],
    'data': [
        'views/mandiri_api_views.xml',
        'security/ir.model.access.csv',
#        'security/RSAPrivKey.pem',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
