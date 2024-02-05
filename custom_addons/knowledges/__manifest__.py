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
        'data/groups.xml',
        'security/ir.model.access.csv',
        'data/rules.xml',
        # 'security/ir.model.access.xml',
        'views/knowledges_menus.xml',
        'views/knowledge_item_views.xml',
    ],
    'installable': True,
    'application': True,
}
