from odoo import (
    models,
    fields,
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
    social_id = fields.Char(
        string='Post ID in Social Media',
        required=False,
        readonly=True
    )
    aggregated_post_id = fields.Many2one(
        'marketing.aggregated.posts',
        string='Aggregated Post Image',
        on_delete='cascade',
        required=False,
    )
    post_id = fields.Many2one(
        'marketing.posts',
        string=' Post Image',
        ondelete='cascade',
        required=False
    )
