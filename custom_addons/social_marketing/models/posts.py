from datetime import datetime
from odoo import (
    models,
    fields,
    api,
)
from odoo.exceptions import ValidationError
from typing import (
    List,
    Dict,
    Any,
)
from ..utils.data_sync_2 import (
    DataSynchronizer2,
)
from ..custom_types import (
    FieldName,
    PostState,
    AccountObject,
    IdType,
)


class PostsWrapper(models.Model):
    _name = 'marketing.posts.wrapper'

    post_ids = fields.One2many(
        'marketing.posts',
        'wrapper_id',
        string='Wrapped Posts',
        required=False,
    )
    total_likes = fields.Integer(
        string='Total Likes',
        compute='_compute_total_likes',
        store=True,
        readonly=True,
    )
    
    @api.depends('post_ids.likes_qty')
    def _compute_total_likes(self) -> int:
        for wrapper in self:
            total_likes = sum(wrapper.post_ids.mapped('likes_qty'))
            wrapper.total_likes = total_likes

    @api.onchange('post_ids')
    def _onchange_post_ids(self) -> None:
        self._compute_total_likes()


class SocialPosts(models.Model):
    _name = 'marketing.posts'
    _description = 'Post Social Account'

    social_id = fields.Char(
        string='Post ID in Social Media',
        required=False, readonly=True)
    message = fields.Char(string='Post Message', required=False)

    schedule_time = fields.Datetime(
        string='Schedule Time Field', required=False,
        default=False)

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
        string='Post State', default=PostState.draft.value)

    likes_qty = fields.Integer(
        string='Number of Likes', default=0, readonly=True)
    reposts_qty = fields.Integer(
        string='Number of Reposts', default=0, readonly=True)
    views_qty = fields.Integer(
        string='Number of Views', default=0, readonly=True)
    comments_qty = fields.Integer(
        string='Number of Comments', default=0, readonly=True)
    
    # changed = fields.Boolean(
    #     string='Is Synced?', default=True, readonly=True)

    account_id = fields.Many2one(
        'marketing.accounts', string='Related Account',
        ondelete='cascade', required=True)
    wrapper_id = fields.Many2one(
        'marketing.posts.wrapper', string='Related Posts Wrapper',
        ondelete='set null', required=False)
    scheduled_action_id = fields.Many2one(
        'ir.cron', string='Related Task',
        ondelete='set null', required=False,
        readonly=True)
    image_ids = fields.One2many(
        'marketing.image', 'post_id',
        string='Post Images', required=False)
    
    now_flag = fields.Boolean(
        string='Schedule', store=True)

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

    def action_update_post(self):
        if self.social_id:
            print('\nАпдейт поста\n')

    def action_create_post(self):
        if not self.social_id:
            # print('\nПроисходит создание поста\n')
            account_list_one_post = self._get_one_account_for_post()
            DataSynchronizer2(['Facebook'], account_list_one_post,
                            self.env['marketing.posts'],
                            self.env['marketing.image'],
                            self.env['marketing.accounts'],
                            ).create_one_post_from_db(self)

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
            acc.id, None, acc.social_media, credentials
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
            acc_obj = AccountObject(acc.id, None, acc.social_media, credentials)
            account_list.append(acc_obj)
        return account_list

    def from_accounts_to_db(self) -> None:
        account_list = self._get_all_account_objects()
        DataSynchronizer2(['Facebook'], account_list,
                         self.env['marketing.posts'],
                         self.env['marketing.image'],
                         self.env['marketing.accounts'],
                         ).from_accounts_to_db()

    def from_db_to_accounts(self) -> None:
        account_list = self._get_all_account_objects()
        DataSynchronizer2(['Facebook'], account_list,
                         self.env['marketing.posts'],
                         self.env['marketing.image'],
                         self.env['marketing.accounts'],
                         ).from_db_to_accounts()

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
        return super(SocialPosts, self).write(values)

    def unlink(self):
        self.scheduled_action_id.unlink()
        return super().unlink()

    def __str__(self) -> str:
        if self.message:
            return self.message[:40]
        return f'Post with ID = {self.id}'
