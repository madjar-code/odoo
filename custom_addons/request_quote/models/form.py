from odoo import models, fields


class RequestQuoteForm(models.Model):
    _name = 'request.quote.form'
    _description = 'Request Quote Form Model'

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='request_quote_form_id',
                              string='Related Lead',
                              ondelete='cascade')
    transportation_type = fields.Char()
    equipment_type = fields.Char()
    vehicle_type = fields.Char()
    note_type = fields.Char()
    note = fields.Text()

    _sql_constraints = (
        ('lead_id_unique', 'UNIQUE(lead_id)',
         'Each Form can be linked to only one CRM Lead.'),
    )
