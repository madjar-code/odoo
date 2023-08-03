from odoo import models, fields


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
