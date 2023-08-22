{
    'name': 'Lead Enrichment',
    'summary': 'Enrich Leads/Opportunities using email address domain',
    'category': 'Sales/CRM',
    'version': '0.1',
    'depends': [
        'crm',
        'mail',
        'enrich_data',
    ],
    'data': (
        'data/ir_action.xml',
        'data/mail_templates.xml',
    ),
    'installable': True,
    'application': True,
}
