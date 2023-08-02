from odoo import models, fields


class Form(models.Model):
    _name = 'stepone.form'
    _description = 'Form Model'

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='form_id',
                              string='Related Lead',
                              ondelete='cascade')
    linkedIn = fields.Char(string='LinkedIn URL')
    file = fields.Char(string='File URL')
    introduction = fields.Text(string='Introduction')

    _sql_constraints = (
        ('lead_id_unique', 'UNIQUE(lead_id)',
         'Each Form can be linked to only one CRM Lead.'),
    )
