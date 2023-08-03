from odoo import models, fields


class DefaultContactForm(models.Model):
    _name = 'default.form'
    _description = 'Default Contact Form Model'

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='default_contact_form_id',
                              string='Related Lead',
                              ondelete='cascade')
    message = fields.Text()

    _sql_constraints = (
        ('lead_id_unique', 'UNIQUE(lead_id)',
         'Each Form can be linked to only one CRM Lead.'),
    )
