from datetime import datetime
from typing import (
    List,
    Optional,
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
    image_ids = fields.One2many(
        'marketing.image',
        'aggregated_post_id',
        string='Aggregated Post Images',
        required=False
    )
    image_ids_changed = fields.Boolean(
        string='Image IDs Changed',
        default=False,
        compute='_compute_image_ids_changed',
        store=True
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

    @api.depends('image_ids')
    def _compute_image_ids_changed(self):
        for agg_post in self:
            if agg_post.state == PostState.posted:
                agg_post.image_ids_changed = True

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
        self.image_ids_changed = False

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
                for image_record in self.image_ids:
                    image_record.copy(
                        {
                            'post_id': new_post.id,
                            'aggregated_post_id': None,
                        }
                    )
                if self.schedule_time:
                    new_post.write({
                        'now_flag': False,
                        'state': PostState.scheduled,
                        'schedule_time': self.schedule_time
                    })
                    new_post.create_schedule_task()
                new_post.image_ids = [(6, 0, new_post.image_ids.ids)]
                self.post_ids += new_post

    def _update_non_published_post(self, post: 'SocialPosts'):
        if post.account_id not in self.account_ids:
            post.unlink()
        else:
            if post.message != self.message:
                post.write({
                    'message': self.message,
                })
            post.image_ids.unlink()
            for image_record in self.image_ids:
                image_record.copy(
                    {
                        'post_id': post.id,
                        'aggregated_post_id': None,
                    }
                )
            post.image_ids = [(6, 0, post.image_ids.ids)]

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

    def _update_published_post(
            self: 'AggregatedPost',
            post: 'SocialPosts'
            ) -> None:
        if self.image_ids_changed:
            post.image_ids.unlink()
            for image_record in self.image_ids:
                image_record.copy(
                    {
                        'post_id': post.id,
                        'aggregated_post_id': None,
                    }
                )
            post.image_ids = [(6, 0, post.image_ids.ids)]
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

    def action_update_statistics(self) -> None:
        post_sync = PostSynchronizer(self.env)
        post_records = self.env['marketing.posts'].search([])
        post_sync.update_post_statistics(post_records)

    def get_social_ids_from_images(self) -> List[IdType]:
        social_ids: List[IdType] = list()
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

# ---------------- CREATE ------------------
    def action_publish_post(self):
        if self.state not in (PostState.posted,
                              PostState.posting):
            if self.state == PostState.scheduled:
                self.scheduled_action_id.unlink()
                self.write({
                    'scheduled_time': False,
                })
            self.write({
                'state': PostState.posting,
            })
            self._create_post_by_id(self.id)
            # self._create_task_for_creation()

    def _create_task_for_creation(self) -> None:
        self.__create_task(
            f'Task For Post Creation {self.id}',
            f'model._create_post_by_id({self.id})',
        )

    def _create_post_by_id(self, post_id: IdType):
        post_record = self.env['marketing.posts'].search([
            ('id', '=', post_id)
        ])
        if not post_record.social_id:
            post_sync = PostSynchronizer(self.env)
            post_sync.create_one_post_db_to_acc(post_record)

    def action_create_post(self):
        if not self.social_id:
            post_sync = PostSynchronizer(self.env)
            post_sync.create_one_post_db_to_acc(self)

# ---------------- UPDATE ------------------
    def action_update_post(self):
        if self.social_id:
            self.write({
                'state': PostState.updating,
            })
            self._create_task_for_updating()

    def _create_task_for_updating(self) -> None:
        self.__create_task(
            f'Task For Updating Post {self.id}',
            f'model._update_post_by_id({self.id})',
        )

    def _update_post_by_id(self, post_id: IdType):
        post_record = self.env['marketing.posts'].search([
            ('id', '=', post_id)
        ])
        post_sync = PostSynchronizer(self.env)
        post_sync.update_one_post_db_to_acc(post_record)

# ---------------- DELETE ------------------
    def action_delete_post(self):
        for post_record in self:
            if post_record.social_id:
                post_record.write({
                    'state': PostState.deleting,
                })
                post_record._create_task_for_deletion()

    def _create_task_for_deletion(self) -> None:
        self.__create_task(
            f'Task For Deletion Post {self.id}',
            f'model._delete_post_by_id({self.id})',
        )

    def _delete_post_by_id(self, post_id: IdType):
        post_record = self.env['marketing.posts'].search([
            ('id', '=', post_id)
        ])
        post_sync = PostSynchronizer(self.env)
        post_sync.delete_one_post_db_to_acc(post_record)
        post_record.unlink()

    def action_pull_comments(self):
        if self.social_id:
            account_object = self._get_one_account_for_post()[0]
            CommentSynchronizer(
                account_object,
                self.social_id,
                self.id,
                self.env,
            ).comments_from_account_to_db()

    def action_push_comments(self):
        if self.social_id:
            account_object = self._get_one_account_for_post()[0]
            CommentSynchronizer(
                account_object,
                self.social_id,
                self.id,
                self.env,
            ).comments_from_db_to_accounts()

    def _get_one_account_for_post(self) -> List[AccountObject]:
        acc = self.account_id
        credentials: Dict[str, str] = dict()
        if acc.social_media == 'Facebook':
            credentials = {
                'access_token': acc.fb_credentials_id.access_token,
                'page_id': acc.fb_credentials_id.page_id,
            }
        elif acc.social_media == 'Instagram':
            credentials = {
                'access_token': acc.inst_credentials_id.access_token,
                'page_id': acc.inst_credentials_id.page_id,
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
            elif acc.social_media == 'Instagram':
                credentials: Dict[str, str] = {
                    'access_token': acc.inst_credentials_id.access_token,
                    'page_id': acc.inst_credentials_id.page_id,
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

    def pull_posts(self) -> None:
        account_db_ids = self.env['marketing.accounts'].search([]).ids
        account_records = self.env['marketing.accounts'].browse(account_db_ids)
        PostSynchronizer(self.env).\
            from_accounts_to_db(account_records)

    def push_posts(self) -> None:
        account_records = self.env['marketing.accounts'].search([])
        PostSynchronizer(self.env).\
            from_db_to_accounts(account_records)

    def create_schedule_task(self) -> None:
        if self.schedule_time:
            scheduled_action = self.__create_task(
                f'Scheduled Post Action for Post {self.id}',
                f'model._create_post_by_id({self.id})',
                None,
                self.schedule_time,
            )
            self.write({
                'scheduled_action_id': scheduled_action.id,
            })
        else:
            raise ValidationError('Have no schedule time')

    def __create_task(
            self,
            task_name: str,
            method_code: str,
            model_id: Optional[IdType] = None,
            call_time: datetime = datetime.now()
            ):
        if not model_id:
            model_id = self.env['ir.model'].\
                search([('model', '=', 'marketing.posts')]).id

        return self.env['ir.cron'].create({
            'name': task_name,
            'model_id': model_id,
            'state': 'code',
            'code': method_code,
            'interval_number': 1,
            'interval_type': 'minutes',
            'nextcall': call_time,
            'numbercall': 1,
            'doall': False,
            'active': True,
        })

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
