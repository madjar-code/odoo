from typing import (
    Optional,
    Union,
    List,
    Dict,
    Any,
)
from ..custom_types import (
    IdType,
    AccountType,
    FieldName,
    AccountObject,
    PostsListType,
    SocialMediaType,
    ErrorType,
    PostObject,
)
from .get.service import GetService
from .post.service import PostService



UPDATE_FIELDS = {
    'message': 'message',
    'reposts_qty': 'reposts_qty',
    'likes_qty': 'likes_qty',
    'comments_qty': 'comments_qty',
}


class DataSynchronizer:
    def __init__(self, social_medias: List[SocialMediaType],
                 account_objects: List[AccountObject], post_table) -> None:
        self.social_medias = social_medias
        self.account_objects = account_objects
        self._post_table = post_table

    def from_accounts_to_db(self) -> None:
        post_table = self._post_table
        existing_social_ids: List[IdType] = self._get_all_social_ids(post_table)
        new_social_ids: List[IdType] = []

        get_service = GetService(self.social_medias, self.account_objects)
        all_posts_api = get_service.get_all_posts_api()
        all_posts_api_filtered = self._filter_non_connected_accounts(all_posts_api)

        account_posts_objects = get_service.process_all_posts(all_posts_api_filtered)
        for page_id in account_posts_objects.keys():
            for post_object in account_posts_objects.get(page_id):
                if post_object.social_id not in existing_social_ids:
                    
                    self._create_non_existent_post(post_object, page_id)
                else:
                    self._update_existing_post(post_object)
                new_social_ids.append((post_object.social_id))
            self._delete_non_existent_posts(existing_social_ids, new_social_ids)

    def _delete_non_existent_posts(self, existing_social_ids: List[IdType],
                                  new_social_ids: List[IdType]) -> None:
        for old_social_id in existing_social_ids:
            if old_social_id not in new_social_ids:
                post_to_delete = self._post_table.search([
                    ('social_id', '=', old_social_id)
                ])
                if post_to_delete:
                    post_to_delete.unlink()

    def _create_non_existent_post(self, post_object: PostObject,
                                  account_id: IdType) -> None:
        post_dict = post_object._asdict()
        post_dict['account_id'] = account_id
        self._post_table.create(post_dict)

    def _update_existing_post(self, post_object: PostObject) -> None:
        existing_post = self._post_table.search([
            ('social_id', '=', post_object.social_id)
        ])
        update_values: Dict[FieldName, Any] = {
            field_db: getattr(post_object, field_db)
            for field_db, field_api in UPDATE_FIELDS.items()
            if getattr(existing_post, field_db) != getattr(post_object, field_api)
        }
        if update_values:
            existing_post.write(update_values)

    def _filter_non_connected_accounts(self, all_posts_api:
            Dict[AccountType, Union[PostsListType, ErrorType]]) ->\
            Dict[AccountType, PostsListType]:
        all_posts_api_filtered: Dict[AccountType, PostsListType] = dict()
        for key, values in all_posts_api.items():
            if not isinstance(values, str):
                all_posts_api_filtered[key] = values
        return all_posts_api_filtered

    def _get_all_social_ids(self, post_table) -> List[IdType]:
        posts = post_table.search_read([], ['social_id'])
        social_ids = [post['social_id'] for post in posts]
        return social_ids

    def from_db_to_accounts(self) -> None:
        non_existent_posts = self._post_table.search([
            ('social_id', '=', False)
        ])
        
        for post in non_existent_posts:
            post_object = PostObject(
                None,
                None,
                None,
                None,
                None,
                post.message,
                post.state,
                post.account_id,
            )
            for acc_obj in self.account_objects:
                if acc_obj.id == post_object.account_id:
                    break
            post_service = PostService('Facebook', acc_obj, post_object=post_object)
            post_errors = post_service.validate_prepare_post_data()
            if not post_errors:
                response_data = post_service.create_post_by_data()
                social_id: Optional[IdType] = response_data.get('id')
                post.write({
                    'social_id': social_id,
                }) if social_id else None

            else:
                return post_errors
