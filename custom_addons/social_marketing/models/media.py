from odoo import (
    api,
    models,
    fields,
)
from odoo.exceptions import ValidationError


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

    # @api.constrains('aggregated_post_id', 'post_id')
    # def _check_post_ids(self):
    #     for image_record in self:
    #         if image_record.aggregated_post_id and\
    #            image_record.post_id:
    #             raise ValidationError("Both 'Aggregated Post Image' and 'Post Image' cannot be set simultaneously.")
