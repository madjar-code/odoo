from odoo import (
    models,
    fields,
    api,
)
from typing import (
    List,
    Dict,
)
# from ..utils.data_sync import (
#     DataSynchronizer,
# )
from ..utils.data_sync_2 import (
    DataSynchronizer2,
)
from ..custom_types import (
    IdType,
    PostState,
    AccountObject,
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
        print(f'\n\SMTH Happends\n\n')
        for wrapper in self:
            total_likes = sum(wrapper.post_ids.mapped('likes_qty'))
            wrapper.total_likes = total_likes

    @api.onchange('post_ids')
    def _onchange_post_ids(self) -> None:
        self._compute_total_likes()


class SocialPosts(models.Model):
    _name = 'marketing.posts'

    social_id = fields.Char(
        string='Post ID in Social Media', required=False)
    message = fields.Char(string='Post Message', required=False)

    schedule_time = fields.Datetime(
        string='Schedule Time Field', required=False)
    state = fields.Selection(
        selection=[(item.value, item.name)
                    for item in PostState],
        string='Post State', default=PostState.draft.value)

    likes_qty = fields.Integer(
        string='Number of Likes', default=0, readonly=True)
    reposts_qty = fields.Integer(
        string='Number of Reposts', default=0, readonly=True)
    views_qty = fields.Integer(
        string='Number of Views', default=0, readonly=True)
    comments_qty = fields.Integer(
        string='Number of Comments', default=0, readonly=True)
    
    changed = fields.Boolean(
        string='Is Synced?', default=True, readonly=True)

    account_id = fields.Many2one(
        'marketing.accounts',
        string='Related Account',
        ondelete='cascade',
    )
    wrapper_id = fields.Many2one(
        'marketing.posts.wrapper',
        string='Related Posts Wrapper',
        ondelete='set null',
        required=False,
    )
    image_ids = fields.One2many(
        'marketing.image',
        'post_id',
        string='Post Images',
        required=False,
    )

    def _get_all_account_objects(self) -> None:
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
                         ).create_new_posts_from_db()

    # def get_all_social_ids(self) -> List[IdType]:
    #     posts = self.env['marketing.posts'].search_read([], ['social_id'])
    #     social_ids = [post['social_id'] for post in posts]
    #     return social_ids
