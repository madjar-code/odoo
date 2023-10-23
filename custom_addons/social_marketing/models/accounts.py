from odoo import (
    models,
    fields,
)
from ..custom_types import SocialMediaType


class Accounts(models.Model):
    _name = 'marketing.accounts'
    _rec_name = 'id_name'

    social_media = fields.Selection(
        selection=[(item.value, item.name)
                   for item in SocialMediaType],
        string='Account Social Media')
    id_name = fields.Char(
        'ID name for account identifying', required=False)
    social_id = fields.Char(
        string='Account ID in Social Media',
        required=False, readonly=False)
    full_name = fields.Char('Full account name')

    post_ids = fields.One2many(
        'marketing.posts',
        'account_id',
        string='Related Account Posts'
    )

    fb_credentials_id = fields.Many2one(
        'marketing.fb.credentials',
        string='Related Credentials Data',
        ondelete='cascade',
        required=False
    )
    _sql_constraints = (
        ('fb_credentials_id_unique', 'UNIQUE(fb_credentials_id)',
         'Each Account can be linked to only one Facebook credentials.'),
    )

    def __str__(self) -> str:
        return self.id_name if self.id_name else self.id


class FacebookCredentials(models.Model):
    _name = 'marketing.fb.credentials'

    access_token = fields.Char(string='Facebook Access Token')
    page_id = fields.Char(string='Facebook Page ID')
    
    account_id = fields.One2many('marketing.accounts',
                                 'fb_credentials_id',
                                 string='Related Account')
