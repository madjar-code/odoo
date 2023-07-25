{
    'name': "Awesome Shirt",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        This app helps you to manage a business of printing customized t-shirts
        for online customers. It offers a public page allowing customers to make
        t-shirt orders.
    """,

    'author': "Odoo",
    'category': 'Technical',
    'version': '1',
    'application': True,
    # 'installable': True,

    'depends': (
        'base',
        'web',
        'mail',
    ),

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'awesome_tshirt/static/src/**/*',
    #     ],
    # },
}