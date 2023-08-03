from odoo import models, fields


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
