from odoo import models, fields, api
from ..custom_types import CommentState


class SocialComment(models.TransientModel):
    _name = 'marketing.comment'
    _description = 'Comment from Social Accounts'

    parent_id = fields.Many2one(
        'marketing.comment',
        string='Parent Comment',
        ondelete='cascade',
        requred=False,
        readonly=True
    )
    parent_social_id = fields.Char(
        string='Comment ID in Social Media',
        required=False,
        readonly=True
    )
    social_id = fields.Char(
        string='Comment ID in Social Media',
        required=False,
        readonly=True
    )
    message = fields.Char(
        string='Comment Message',
        required=True
    )
    author_id = fields.Char(
        string='Author String Indentificator', 
        readonly=True,
        required=False
    )
    post_id = fields.Many2one(
        'marketing.posts',
        string='Related Post',
        ondelete='cascade',
        requred=False,
        readonly=True
    )
    posted_time = fields.Datetime(
        string='Posted Time',
        store=True,
        readonly=True
    )
    state = fields.Selection(
        selection=[(item.value, item.name)
                   for item in CommentState],
        readonly=True,
        string='Comment State',
        default=CommentState.draft
    )
    has_account_relation = fields.Boolean(
        string='Is Our Account Comment',
        compute='_compute_has_account_relation',
        store=True,
        default=True,
    )
    has_lead_comment = fields.Boolean(
        string='Has Lead Comment',
        compute='_compute_has_lead_comment',
        default=False,
        store=True
    )

    @api.depends('author_id')
    def _compute_has_account_relation(self):
        for comment in self:
            if comment.author_id:
                account = self.env['marketing.accounts'].search([
                    ('social_id', '=', comment.author_id),
                ], limit=1)
                comment.has_account_relation = bool(account)
            else:
                comment.has_account_relation = True

    @api.depends('social_id')
    def _compute_has_lead_comment(self):
        for comment in self:
            if comment.social_id:
                lead_comment = self.env['marketing.lead.comment'].search([
                    ('social_id', '=', comment.social_id),
                ], limit=1)
                comment.has_lead_comment = bool(lead_comment)
            else:
                comment.has_lead_comment = False

    def __str__(self) -> str:
        if self.message:
            return self.message[:40]
        return f'Comment with ID = {self.id}'

    def action_create_lead(self):
        lead = self.env['crm.lead'].create({
            'name': f'Comment Lead for {self.social_id}',
            'description': f'Comment Message: {self.message}<br/><br/>'\
                           f'Author Link: <a href="https://www.facebook.com/profile.php?id={self.author_id}">Click Here</a>'
        })
        prop_description = self.env['crm.prop.description'].search([
            ('name', '=', 'facebook')
        ], limit=1)

        page_link = f'https://www.facebook.com/profile.php?id={self.author_id}'

        if not prop_description:
            prop_description = self.env['crm.prop.description'].create({
                'name': 'facebook',
                'prop_type': 'char'
            })

        self.env['crm.prop.value'].create({
            'value': page_link,
            'prop_description_id': prop_description.id,
            'lead_id': lead.id
        })

        if self.post_id:
            self.env['marketing.lead.comment'].create({
                'social_id': self.social_id,
                'message': self.message,
                'author_id': self.author_id,
                'post_id': self.post_id.id,
                'lead_id': lead.id,
            })
            self.write({
                'has_lead_comment': True,
            })
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'view_mode': 'form',
                'res_id': lead.id,
            }

    def action_go_to_lead(self) -> None:
        lead_comment = self.env['marketing.lead.comment'].search(
            [('social_id', '=', self.social_id)]
        )
        if lead_comment:
            lead_id = lead_comment.lead_id
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'view_mode': 'form',
                'res_id': lead_id.id,
            }


class LeadComment(models.Model):
    _name = 'marketing.lead.comment'
    _description = 'Lead Comment from Accounts'

    social_id = fields.Char(
        string='Comment ID in Social Media',
        required=True,
        readonly=True,
    )
    message = fields.Char(
        string='Comment Message',
        required=False
    )
    author_id = fields.Char(
        string='Author String Indentificator',
        required=False,
    )
    post_id = fields.Many2one(
        'marketing.posts',
        string='Related Post',
        ondelete='cascade',
        requred=False,
    )
    lead_id = fields.Many2one(
        'crm.lead',
        string='Related Lead',
        ondelete='cascade',
        required=True
    )

    def __str__(self) -> str:
        return f'Lead Comment: {self.id} - {self.lead_id.id}'

    def unlink(self):
        transient_comment = self.env['marketing.comment'].search([
            ('social_id', '=', self.social_id)
        ], limit=1)
        transient_comment.write({
            'has_lead_comment': False,
        })
        return super().unlink()
