from odoo import models, fields


class InstantForm(models.Model):
    _name = 'instant.form'
    _description = 'Instant Form Model'

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='instant_form_id',
                              string='Related Lead',
                              ondelete='cascade')
    transport_car_from = fields.Char()
    transport_car_to = fields.Char()
    transport_car_type = fields.Char()

    _sql_constraints = (
        ('lead_id_unique', 'UNIQUE(lead_id)',
         'Each Form can be linked to only one CRM Lead.'),
    )
