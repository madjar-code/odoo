from datetime import datetime
from typing import (
    List,
    Dict,
    Any,
)
from odoo import (
    models,
    fields,
    api,
)
from odoo.exceptions import ValidationError
from ..utils.comment_sync import CommentSynchronizer
from ..utils.post_sync import PostSynchronizer
from ..custom_types import (
    FieldName,
    PostState,
    AccountObject,
    IdType,
)


class AggregatedPost(models.Model):
    _name = 'marketing.aggregated.posts'
    _description = 'Aggregated Post'
    _rec_name = 'message'
    _rec_names_search = (
        'message',
    )
    account_ids = fields.Many2many(
        comodel_name='marketing.accounts',
        relation='aggregated_posts_accounts_rel',
        string='Related Accounts'
    )
    post_ids = fields.One2many(
        comodel_name='marketing.posts',
        inverse_name='aggregated_post_id',
        string='Related Posts',
        readonly=True
    )
    state = fields.Selection(
        selection=[(item.value, item.name)
                    for item in PostState],
        compute='_compute_state',
        string='Aggregate State',
        default=PostState.draft.value
    )
    message = fields.Char(string='Posts Message', required=True)
    now_flag = fields.Boolean(string='Schedule', store=True)
    schedule_time = fields.Datetime(
        string='Schedule Time Field',
        required=False,
        default=False,
    )

    @api.onchange('schedule_time')
    def _onchange_schedule_time(self):
        for agg_post in self:
            if agg_post.schedule_time and datetime.now() > agg_post.schedule_time:
                raise ValidationError('Schedule time cannot be in the past.')

    @api.depends('post_ids.state')
    def _compute_state(self):
        for agg_post in self:
            states: List[PostState] = agg_post.post_ids.mapped('state')
            states_set = set(states)
            if len(states_set) == 1:
                agg_state = states_set.pop()
            elif len(states_set) == 0:
                agg_state = PostState.draft.value
            else:
                agg_state = PostState.mixed.value
            agg_post.write({
                'state': agg_state
            })

    def action_initialize_posts(self):
        self._initialize_posts_for_new_accs()
        self.env['marketing.stat.groups'].create({
            'title': f'Group for Aggregate - {self.id}',
            'post_ids': self.post_ids if self.post_ids else [],
        })

    def action_update_posts(self):
        self._initialize_posts_for_new_accs()
        for post in self.post_ids:
            if post.state != PostState.posted:
                self._update_non_published_post(post)
            else:
                self._update_published_post(post)

    def _initialize_posts_for_new_accs(self):
        for account in self.account_ids:
            existing_post = self.post_ids.filtered(
                lambda post: post.account_id == account
            )
            if not existing_post:
                new_post = self.env['marketing.posts'].create({
                    'account_id': account.id,
                    'message': self.message,
                    'aggregated_post_id': self.id,
                })
                if self.schedule_time:
                    new_post.write({
                        'now_flag': False,
                        'state': PostState.scheduled,
                        'schedule_time': self.schedule_time
                    })
                    new_post.create_schedule_task()
                self.post_ids += new_post

    def _update_non_published_post(self, post: 'SocialPosts'):
        if post.account_id not in self.account_ids:
            post.unlink()
        else:
            if post.message != self.message:
                post.write({
                    'message': self.message,
                })

            if not post.schedule_time and self.schedule_time:
                post.write({
                    'now_flag': False,
                    'state': PostState.scheduled,
                    'schedule_time': self.schedule_time
                })
                post.create_schedule_task()
            elif not self.schedule_time and post.schedule_time:
                post.scheduled_action_id.unlink()
                post.write({
                    'now_flag': True,
                    'state': PostState.draft,
                    'schedule_time': False
                })
            elif self.schedule_time != post.schedule_time:
                post.write({
                    'schedule_time': self.schedule_time,
                })

    def _update_published_post(self: 'AggregatedPost',
                               post: 'SocialPosts'):
        if post.message != self.message:
            post.write({
                'message': self.message,
            })
            post.action_update_post()

    def action_publish_posts(self):
        for post in self.post_ids:
            post.action_publish_post()

    def unlink(self):
        for post in self.post_ids:
            if post.state != PostState.posted.value:
                post.unlink()
        return super().unlink()


class SocialPosts(models.Model):
    _name = 'marketing.posts'
    _description = 'Post Social Account'
    _rec_name = 'message'

    social_id = fields.Char(
        string='Post ID in Social Media',
        required=False,
        readonly=True
    )
    message = fields.Char(string='Post Message', required=False)

    schedule_time = fields.Datetime(
        string='Schedule Time Field',
        required=False,
        default=False
    )
    posted_time = fields.Datetime(
        string='Posted Time',
        # compute='_compute_posted_time',
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        selection=[(item.value, item.name)
                    for item in PostState],
        readonly=True,
        string='Post State',
        default=PostState.draft.value
    )
    likes_qty = fields.Integer(
        string='Number of Likes',
        default=0,
        readonly=True
    )
    reposts_qty = fields.Integer(
        string='Number of Reposts',
        default=0,
        readonly=True
    )
    views_qty = fields.Integer(
        string='Number of Views',
        default=0,
        readonly=True
    )
    comments_qty = fields.Integer(
        string='Number of Comments',
        default=0,
        readonly=True
    )
    # changed = fields.Boolean(
    #     string='Is Synced?', default=True, readonly=True)
    account_id = fields.Many2one(
        'marketing.accounts',
        string='Related Account',
        ondelete='cascade',
        required=True
    )
    aggregated_post_id = fields.Many2one(
        comodel_name='marketing.aggregated.posts',
        string='Related Aggregated Post',
        ondelete='set null',
        required=False,
    )
    stat_group_id = fields.Many2one(
        comodel_name='marketing.stat.groups',
        string='Related Statistic Group',
        ondelete='set null',
        required=False,
    )
    scheduled_action_id = fields.Many2one(
        'ir.cron',
        string='Related Task',
        ondelete='set null',
        required=False,
        readonly=True
    )
    image_ids = fields.One2many(
        'marketing.image',
        'post_id',
        string='Post Images',
        required=False
    )
    comment_ids = fields.One2many(
        'marketing.comment',
        'post_id',
        string='Social Comments',
        required=False
    )

    lead_comment_ids = fields.One2many(
        'marketing.lead.comment',
        'post_id',
        string='Lead Comments',
        required=False
    )

    now_flag = fields.Boolean(string='Schedule', store=True)

    def get_social_ids_from_images(self) -> List[IdType]:
        social_ids: List[IdType] = []
        for post in self:
            for image in post.image_ids:
                if image.social_id:
                    social_ids.append(image.social_id)
        return social_ids

    @api.onchange('schedule_time')
    def _onchange_schedule_time(self):
        for post in self:
            if post.schedule_time and datetime.now() > post.schedule_time:
                raise ValidationError('Schedule time cannot be in the past.')
    
    def action_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'marketing.posts',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'target': 'current',
        }

    def action_finish_later(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'marketing.posts',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def action_aggregate_unpin_post(self):
        for post in self:
            for account in post.account_id:
                post.aggregated_post_id.write({
                    'account_ids': [(3, account.id, 0)]
                })
            post.write({
                'aggregated_post_id': False,
            })

    def action_publish_post(self):
        if self.state in (PostState.draft,
                          PostState.failed):
            self.action_create_post()
        elif self.state == PostState.scheduled:
            self.action_create_post()
            self.scheduled_action_id.unlink()
            self.write({
                'schedule_time': False,
            })

    def action_pull_comments(self):
        if self.social_id:
            account_object = self._get_one_account_for_post()[0]
            CommentSynchronizer(
                account_object,
                self.social_id,
                self.id,
                self.env['marketing.comment'],
                self.env['marketing.posts']
            ).comments_from_account_to_db()

    def action_push_comments(self):
        if self.social_id:
            account_object = self._get_one_account_for_post()[0]
            CommentSynchronizer(
                account_object,
                self.social_id,
                self.id,
                self.env['marketing.comment'],
                self.env['marketing.posts'],
                self.env['crm.lead'],
            ).comments_from_db_to_accounts()

    def action_update_post(self):
        if self.social_id:
            post_sync = PostSynchronizer(
                self.env['marketing.image'],
                self.env['marketing.posts'],
                self.env['marketing.stat.groups'],
            )
            post_sync.update_one_post_db_to_acc(self)

    def action_create_post(self):
        if not self.social_id:
            post_sync = PostSynchronizer(
                self.env['marketing.image'],
                self.env['marketing.posts'],
                self.env['marketing.stat.groups'],
            )
            post_sync.create_one_post_db_to_acc(self)

    def action_delete_post(self):
        if self.social_id:
            post_sync = PostSynchronizer(
                self.env['marketing.image'],
                self.env['marketing.posts'],
                self.env['marketing.stat.groups'],
            )
            post_sync.delete_one_post_db_to_acc(self)
            self.unlink()

    def _create_post_by_id(self, post_id: IdType):
        post_object = self.env['marketing.posts'].search([
            ('id', '=', post_id)
        ])
        post_object.action_create_post()

    def _get_one_account_for_post(self) -> List[AccountObject]:
        acc = self.account_id
        credentials: Dict[str, str] = dict()
        if acc.social_media == 'Facebook':
            credentials = {
                'access_token': acc.fb_credentials_id.access_token,
                'page_id': acc.fb_credentials_id.page_id,
            }
        account_object = AccountObject(
            acc.id,
            None,
            acc.social_id,
            acc.social_media,
            credentials
        )
        return [account_object]

    def _get_all_account_objects(self) -> List[AccountObject]:
        accounts = self.env['marketing.accounts'].search([])
        account_list: List[AccountObject] = []
        for acc in accounts:
            if acc.social_media == 'Facebook':
                credentials: Dict[str, str] = {
                    'access_token': acc.fb_credentials_id.access_token,
                    'page_id': acc.fb_credentials_id.page_id,
                }
            acc_obj = AccountObject(
                acc.id,
                None,
                acc.social_id,
                acc.social_media,
                credentials
            )
            account_list.append(acc_obj)
        return account_list

    def from_accounts_to_db(self) -> None:
        account_records = self.env['marketing.accounts'].search([])
        PostSynchronizer(
            self.env['marketing.image'],
            self.env['marketing.posts'],
            self.env['marketing.stat.groups'],
        ).from_accounts_to_db(account_records)

    def from_db_to_accounts(self) -> None:
        account_records = self.env['marketing.accounts'].search([])
        PostSynchronizer(
            self.env['marketing.image'],
            self.env['marketing.posts'],
            self.env['marketing.stat.groups'],
        ).from_db_to_accounts(account_records)

    def create_schedule_task(self) -> None:
        if self.schedule_time:
            scheduled_action = self.env['ir.cron'].create({
                'name': f'Scheduled Post Action for Post {self.id}',
                'model_id': self.env['ir.model'].search([('model', '=', 'marketing.posts')]).id,
                'state': 'code',
                'code': f'model._create_post_by_id({self.id})',
                'interval_number': 1,
                'interval_type': 'minutes',
                'nextcall': self.schedule_time,
                'numbercall': 1,
                'doall': False,
                'active': True,
            })
            self.write({
                'scheduled_action_id': scheduled_action.id,
            })
        else:
            raise ValidationError('Have no schedule time')

    def write(self, values: Dict[FieldName, Any]):
        if 'schedule_time' in values and self.scheduled_action_id:
            new_schedule_time_str = values.get('schedule_time')
            new_schedule_time = fields.Datetime.from_string(new_schedule_time_str)
            if new_schedule_time and new_schedule_time < fields.Datetime.now():
                raise ValidationError('Schedule time is in the past')
            self.scheduled_action_id.write(
                {'nextcall': new_schedule_time,}
            )
        if 'message' in values and self.aggregated_post_id:
            new_message = values.get('message')
            if new_message != self.aggregated_post_id.message:
                self.action_aggregate_unpin_post()
        return super(SocialPosts, self).write(values)

    def unlink(self):
        if self.scheduled_action_id:
            self.scheduled_action_id.unlink()
        if self.aggregated_post_id:
            self.action_aggregate_unpin_post()
        return super().unlink()

    def __str__(self) -> str:
        if self.message:
            return self.message[:40]
        return f'Post with ID = {self.id}'
