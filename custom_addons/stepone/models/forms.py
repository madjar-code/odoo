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
    
    TRANSPORT_CAR_TYPES = (
        ('Car', 'Car'),
        ('SUV', 'SUV'),
        ('Pickup', 'Pickup'),
        ('Van', 'Van'),
        ('RV', 'RV'),
        ('Moto', 'Moto'),
        ('Heavy Equipment', 'Heavy Equipment'),
        ('General Freight', 'General Freight'),
    )

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='instant_form_id',
                              string='Related Lead',
                              ondelete='cascade')
    transport_car_from = fields.Char()
    transport_car_to = fields.Char()
    transport_car_type = fields.Selection(selection=TRANSPORT_CAR_TYPES,
                                          string='Transport Car Types')

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

    TRANSPORTATION_TYPES = (
        ('Door-to-door', 'Door-to-door'),
        ('Terminal-to-terminal', 'Terminal-to-terminal'),
    )
    EQUIPMENT_TYPES = (
        ('Open Car Hauler', 'Open Car Hauler'),
        ('Enclosed Car Hauler', 'Enclosed Car Hauler'),
        ('General or Large Freight', 'General or Large Freight'),
    )
    VEHICLE_TYPES = (
        ('Car', 'Car'),
        ('SUV', 'SUV'),
        ('Pickup', 'Pickup'),
        ('Van', 'Van'),
        ('Moto', 'Moto'),
        ('ATV', 'ATV'),
        ('RV', 'RV'),
        ('Heavy Equipment', 'Heavy Equipment'),
        ('Large Yacht', 'Large Yacht'),
        ('Travel Trailer', 'Travel Trailer'),
    )

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='request_quote_form_id',
                              string='Related Lead',
                              ondelete='cascade')

    transportation_type = fields.Selection(selection=TRANSPORTATION_TYPES,
                                           string='Transportation Type')
    equipment_type = fields.Selection(selection=EQUIPMENT_TYPES,
                                      string='Equipment Type')
    vehicle_type = fields.Selection(selection=VEHICLE_TYPES,
                                    string='Vehicle Type')
    note = fields.Text()

    _sql_constraints = (
        ('lead_id_unique', 'UNIQUE(lead_id)',
         'Each Form can be linked to only one CRM Lead.'),
    )


class ReviewForm(models.Model):
    _name = 'review.form'
    _description = 'Review Form Model'
    
    RATE_CHOICES = (
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
    )

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='review_form_id',
                              string='Related Lead',
                              ondelete='cascade')
    rate = fields.Selection(
        selection=RATE_CHOICES, string='Rate', required=True,)

    _sql_constraints = (
        ('lead_id_unique', 'UNIQUE(lead_id)',
         'Each Form can be linked to only one CRM Lead.'),
    )
