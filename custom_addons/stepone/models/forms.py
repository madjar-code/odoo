from enum import Enum
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


class TransportCarType(str, Enum):
    car = 'Car'
    suv = 'SUV'
    pickup = 'Pickup'
    van = 'Van'
    moto = 'Moto'
    rv = 'RV'
    heavy_equipment = 'Heavy Equipment'
    general_freight = 'General Freight'


class InstantForm(models.Model):
    _name = 'instant.form'
    _description = 'Instant Form Model'

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='instant_form_id',
                              string='Related Lead',
                              ondelete='cascade')
    transport_car_from = fields.Char()
    transport_car_to = fields.Char()
    transport_car_type = fields.Selection(
        selection=[(item.value, item.name)
                   for item in TransportCarType],
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


class TransportationType(str, Enum):
    D2D = 'Door-to-door'
    T2T = 'Terminal-to-terminal'


class EquipmentType(str, Enum):
    open_car_hauler = 'Open Car Hauler'
    enclosed_car_hauler = 'Enclosed Car Hauler'
    general_or_large_freight = 'General or Large Freight'


class VehicleType(str, Enum):
    car = 'Car'
    suv = 'SUV'
    pickup = 'Pickup'
    van = 'Van'
    moto = 'Moto'
    atv = 'ATV'
    rv = 'RV'
    heavy_equipment = 'Heavy Equipment'
    large_yacht = 'Large Yacht'
    travel_trailer = 'Travel Trailer'


class RequestQuoteForm(models.Model):
    _name = 'request.quote.form'
    _description = 'Request Quote Form Model'

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='request_quote_form_id',
                              string='Related Lead',
                              ondelete='cascade')

    transportation_type = fields.Selection(
        selection=[(item.value, item.name)
                   for item in TransportationType],
        string='Transportation Type'
    )
    equipment_type = fields.Selection(
        selection=[(item.value, item.name)
                   for item in EquipmentType],
        string='Equipment Type'
    )
    vehicle_type = fields.Selection(
        selection=[(item.value, item.name)
                   for item in VehicleType],
        string='Vehicle Type'
    )
    note = fields.Text()

    _sql_constraints = (
        ('lead_id_unique', 'UNIQUE(lead_id)',
         'Each Form can be linked to only one CRM Lead.'),
    )


class RateChoice(str, Enum):
    one = '1'
    two = '2'
    three = '3'
    four = '4'
    five = '5'
    six = '6'
    seven = '7'
    eight = '8'
    nine = '9'
    ten = '10'


class ReviewForm(models.Model):
    _name = 'review.form'
    _description = 'Review Form Model'

    lead_id = fields.Many2one('crm.lead',
                              inverse_name='review_form_id',
                              string='Related Lead',
                              ondelete='cascade')
    rate = fields.Selection(
        selection=[(item.value, item.name)
                   for item in RateChoice],
        string='Rate', required=True,
    )
    _sql_constraints = (
        ('lead_id_unique', 'UNIQUE(lead_id)',
         'Each Form can be linked to only one CRM Lead.'),
    )
