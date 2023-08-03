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


class QuestionForm(models.Model):
    _name = 'question.form'
    _description = 'Question Form Model'

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='question_form_id',
                              string='Related Lead',
                              ondelete='cascade')
    communication_with = fields.Char(string='With whom to communicate')
    message = fields.Text(string='Message to Server')

    _sql_constraints = (
        ('lead_id_unique', 'UNIQUE(lead_id)',
         'Each Form can be linked to only one CRM Lead.'),
    )


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


class ReviewForm(models.Model):
    _name = 'review.form'
    _description = 'Review Form Model'

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='review_form_id',
                              string='Related Lead',
                              ondelete='cascade')
    rate = fields.Char()

    _sql_constraints = (
        ('lead_id_unique', 'UNIQUE(lead_id)',
         'Each Form can be linked to only one CRM Lead.'),
    )
