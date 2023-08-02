from odoo import models, fields


class Form(models.Model):
    _name = 'stepone.form'
    _description = 'Form Model'

    linkedIn = fields.Char(string='LinkedIn URL')
    file = fields.Char(string='File URL')
    introduction = fields.Text(string='Introduction')
