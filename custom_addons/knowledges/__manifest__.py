{
    'name': 'Knowledges',
    'summary': 'Documents for helping in job',
    'description': '',
    'category': 'Services',
    'version': '0.1',
    'depends': [
        'web',
        'base',
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'views/assets.xml',
        'views/knowledges_menus.xml',
        'views/knowledge_item_views.xml',
    ],
    'installable': True,
    'application': True,
}
