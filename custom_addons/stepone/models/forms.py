from ..choices import *
from odoo import models, fields


class AbstractForm(models.AbstractModel):
    _name = 'abstract.form'
    _description = 'Abstact form with related-field'

    lead_id = fields.Many2one('crm.lead',
                              string='Related Lead',
                              ondelete='cascade')
    _sql_constraints = (
        ('lead_id_unique', 'UNIQUE(lead_id)',
         'Each Form can be linked to only one CRM Lead.'),
    )


class SteponeForm(models.Model):
    _name = 'stepone.form'
    _inherit = 'abstract.form'

    linkedIn = fields.Char(string='LinkedIn URL')
    file = fields.Char(string='File URL')
    introduction = fields.Text(string='Introduction')


class DefaultContactForm(models.Model):
    _name = 'default.form'
    _inherit = 'abstract.form'
    _description = 'Default Contact Form Model'

    message = fields.Text()


class InstantForm(models.Model):
    _name = 'instant.form'
    _inherit = 'abstract.form'
    _description = 'Instant Form Model'

    transport_car_from = fields.Char()
    transport_car_to = fields.Char()
    transport_car_type = fields.Selection(
        selection=[(item.value, item.name)
                   for item in TransportCarType],
        string='Transport Car Types')


class QuestionForm(models.Model):
    _name = 'question.form'
    _inherit = 'abstract.form'
    _description = 'Question Form Model'

    communication_with = fields.Char(string='With whom to communicate')
    message = fields.Text(string='Message to Server')


class RequestQuoteForm(models.Model):
    _name = 'request.quote.form'
    _inherit = 'abstract.form'
    _description = 'Request Quote Form Model'

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


class ReviewForm(models.Model):
    _name = 'review.form'
    _inherit = 'abstract.form'
    _description = 'Review Form Model'

    rate = fields.Selection(
        selection=[(item.value, item.name)
                   for item in RateChoice],
        string='Rate', required=True,
    )


class SpecialService(models.Model):
    _name = 'get.quote.form.services'

    name = fields.Char()
    value = fields.Integer()


class GetQuoteForm(models.Model):
    _name = 'get.quote.form'
    _inherit = 'abstract.form'
    _description = 'Get A Quote Form'

    first_name = fields.Char()
    company_name = fields.Char()
    email = fields.Char()
    phone = fields.Char()
    
    description = fields.Text()
    size = fields.Integer(string='Size, ft')
    weight = fields.Integer(string='Weight, lbs')

    origin_address = fields.Text()
    origin_zip_code = fields.Char()
    origin_city = fields.Char()
    origin_state = fields.Char()

    destination_address = fields.Text()
    destination_zip_code = fields.Char()
    destination_city = fields.Char()
    destination_state = fields.Char()

    special_service_ids = fields.Many2many(
        comodel_name='get.quote.form',
        relation='get_quote_form_service',
    )
