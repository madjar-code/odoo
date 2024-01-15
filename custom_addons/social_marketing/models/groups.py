from odoo import (
    models,
    fields,
    api,
)
from ..custom_types import PostState
from ..utils.post_sync import PostSynchronizer


class StatGroup(models.Model):
    _name = 'marketing.stat.groups'
    _description = 'Post Statistics Group'
    _rec_name = 'title'
    _rec_names_search = (
        'title',
    )
    account_ids = fields.Many2many(
        readonly=True,
        compute='_compute_account_ids',
        comodel_name='marketing.accounts',
        relation='stat_groups_accounts_rel',
        string='Related Accounts',
    )
    post_ids = fields.One2many(
        comodel_name='marketing.posts',
        inverse_name='stat_group_id',
        string='Related Posts',
    )
    title = fields.Char(string='Group Title', required=True)

    likes_qty = fields.Integer(
        default=0,
        readonly=True,
        compute='_compute_likes_qty',
        string='Number of Likes',
    )
    reposts_qty = fields.Integer(
        default=0,
        compute='_compute_reposts_qty',
        readonly=True,
        string='Number of Reposts',
    )
    comments_qty = fields.Integer(
        default=0,
        readonly=True,
        compute='_compute_comments_qty',
        string='Number of Comments',
    )

    @api.depends('post_ids.likes_qty')
    def _compute_likes_qty(self):
        for stat_group in self:
            likes_qty = sum(post.likes_qty for post in stat_group.post_ids)
            stat_group.likes_qty = likes_qty

    @api.depends('post_ids.reposts_qty')
    def _compute_reposts_qty(self):
        for stat_group in self:
            reposts_qty = sum(post.reposts_qty for post in stat_group.post_ids)
            stat_group.reposts_qty = reposts_qty

    @api.depends('post_ids.comments_qty')
    def _compute_comments_qty(self):
        for stat_group in self:
            comments_qty = sum(post.comments_qty for post in stat_group.post_ids)
            stat_group.comments_qty = comments_qty

    @api.depends('post_ids.account_id')
    def _compute_account_ids(self):
        for stat_group in self:
            account_ids = stat_group.post_ids.mapped('account_id').ids
            stat_group.account_ids = [(6, 0, account_ids)]

    def action_update_data(self):
        post_sync = PostSynchronizer(self.env)
        posted_post_records = self.env['marketing.posts'].search([
            ('state', '=', PostState.posted),
            ('stat_group_id', '=', self.id),
        ])
        post_sync.update_post_list_acc_to_db(posted_post_records)
