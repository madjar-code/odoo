import os
from odoo import (
    models,
    fields,
    api,
)


class Media(models.AbstractModel):
    _name = 'marketing.media'
    _description = 'Abstract Media'
    
    name = fields.Char(string='Name')
    description = fields.Text(string='Description')


class Image(models.Model):
    _name = 'marketing.image'
    _description = 'Image Media'
    _inherit = 'marketing.media'

    image = fields.Image(
        string='Image Data',
        attachment=True
    )

    post_id = fields.Many2one(
        'marketing.posts',
        string='Image Post',
        ondelete='cascade',
        required=False
    )
