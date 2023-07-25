{
    'name': 'CRM Lead checkbox',
    'version': '1',
    'summary': 'Create checkboxes for Leads/Opportunities based on user config',
    # 'category': 'Sales/CRM',
    'description': '',
    'application': True,
    'installable': True,
    'depends': (
        'web',
        'crm',
    ),
    'data': (
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/crm_lead_form_view.xml',
        'views/checklist_views.xml',
        'views/res_users_views.xml',
        'views/templates.xml',
    ),
    'qweb': (
        'static/src/xml/widget_template.xml',
    )
}