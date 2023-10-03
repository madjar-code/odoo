import io
import base64
from PIL import Image
from typing import (
    Optional,
    Union,
    Tuple,
    List,
    Dict,
    Any,
)
from odoo.models import fields
from ..custom_types import (
    IdType,
    AccountType,
    FieldName,
    AccountObject,
    PostsListType,
    SocialMediaType,
    ErrorType,
    PostObject,
    ImageObject,
    PostState,
)
from .get.service import GetService
from .post.service import PostService
from .delete.service import DeleteService


UPDATE_FIELDS = {
    'message': 'message',
    'reposts_qty': 'reposts_qty',
    'likes_qty': 'likes_qty',
    'comments_qty': 'comments_qty',
}


class DataSynchronizer2:
    def __init__(self, social_medias: List[SocialMediaType],
                 account_objects: List[AccountObject],
                 post_table, image_table, account_table) -> None:
        self.social_medias = social_medias
        self.account_objects = account_objects
        self._post_table = post_table
        self._account_table = account_table
        self._image_table = image_table

    def _get_account_posts_objects(self) ->\
            Dict[AccountType, List[PostObject]]:
        get_service = GetService(self.social_medias, self.account_objects)
        all_posts_api = get_service.get_all_posts_api()

        all_posts_api_filtered = self._filter_non_connected_accounts(all_posts_api)
        account_posts_objects = get_service.process_all_posts(all_posts_api_filtered)
        return account_posts_objects

    def from_accounts_to_db(self) -> None:
        existing_social_ids: List[IdType] = self._get_all_social_ids()
        new_social_ids: List[IdType] = []

        account_posts_objects = self._get_account_posts_objects()

        for page_id in account_posts_objects.keys():
            for post_object in account_posts_objects.get(page_id):
                if post_object.social_id not in existing_social_ids:
                    self._create_non_existent_post(post_object, page_id)
                else:
                    self._update_existing_post(post_object)
                new_social_ids.append(post_object.social_id)
        self._delete_non_existent_posts(existing_social_ids, new_social_ids)

    def create_new_posts_from_accounts(self) -> None:
        account_posts_objects = self._get_account_posts_objects()
        for page_id in account_posts_objects.keys():
            for post_object in account_posts_objects.get(page_id):
                self._create_non_existent_post(post_object, page_id)

    def update_old_posts_from_accounts(self) -> None:
        existing_social_ids: List[IdType] = self._get_all_social_ids()
        account_posts_objects = self._get_account_posts_objects()
        for page_id in account_posts_objects.keys():
            for post_object in account_posts_objects.get(page_id):
                if post_object.social_id in existing_social_ids:
                    self._update_existing_post(post_object, page_id)

    def delete_old_posts_from_accounts(self) -> None:
        existing_social_ids: List[IdType] = self._get_all_social_ids()
        new_social_ids: List[IdType] = []
        account_posts_objects = self._get_account_posts_objects()
        for page_id in account_posts_objects.keys():
            for post_object in account_posts_objects.get(page_id):
                new_social_ids.append(post_object.social_id)
        self._delete_non_existent_posts(existing_social_ids, new_social_ids)

    def _get_all_social_ids(self) -> List[IdType]:
        posts = self._post_table.search_read([], ['social_id'])
        social_ids = [post['social_id'] for post in posts]
        return social_ids
 
    def _filter_non_connected_accounts(self, all_posts_api:
            Dict[AccountType, Union[PostsListType, ErrorType]]) ->\
            Dict[AccountType, PostsListType]:
        all_posts_api_filtered: Dict[AccountType, PostsListType] = dict()
        for key, values in all_posts_api.items():
            if not isinstance(values, str):
                all_posts_api_filtered[key] = values
            else:
                raise Exception(f'\nAccount Connection Problem\n')
        return all_posts_api_filtered

    def _create_non_existent_post(self, post_object: PostObject,
                                  account_id: IdType) -> None:
        post_dict = post_object._asdict()
        del post_dict['image_objects']
        post_dict['account_id'] = account_id
        new_post = self._post_table.create(post_dict)
        for image_object in post_object.image_objects:
            try:
                image_data = {
                    'name': image_object.name,
                    'description': image_object.description,
                    'image': image_object.image,
                    'post_id': new_post.id,
                }
                self._image_table.create(image_data)
            except Exception as e:
                print(e)

    def _update_existing_post(self, post_object: PostObject) -> None:
        try:
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
                old_related_images = self._image_table.search([
                    ('post_id', '=', existing_post.id)
                ])

            # if content was updated recreate new images
            if update_values.get('message'):
                for old_image in old_related_images:
                    old_image.unlink()

                for image_object in post_object.image_objects:
                    image_data = {
                        'name': image_object.name,
                        'description': image_object.description,
                        'image': image_object.image,
                        'post_id': existing_post.id,
                    }
                    self._image_table.create(image_data)
        except Exception as e:
            print(e)

    def _delete_non_existent_posts(self, existing_social_ids: List[IdType],
                                   new_social_ids: List[IdType]) -> None:
        for old_social_id in existing_social_ids:
            if old_social_id not in new_social_ids:
                post_to_delete = self._post_table.search([
                    ('social_id', '=', old_social_id)
                ])
                if post_to_delete:
                    post_to_delete.unlink()

    def from_db_to_accounts(self) -> None:
        self.create_new_posts_from_db()
        self.delete_old_posts_from_db()

    def create_new_posts_from_db(self):
        non_existent_posts = self._post_table.search([
            ('social_id', '=', False)
        ])

        for post in non_existent_posts:
            self.create_one_post_from_db(post)

    def create_one_post_from_db(self, post_db_object) ->\
            Optional[Dict[FieldName, List[ErrorType]]]:
        related_images = self._image_table.search([
            ('post_id', '=', post_db_object.id)
        ])
        image_objects: List[ImageObject] = []

        for related_image in related_images:
            if related_image.image:
                image_format, image_bytes_io = self._process_image_data(
                    base64.b64decode(related_image.image)
                )
                image_object = ImageObject(
                    name=f'image.{image_format}',
                    description=None,
                    format=image_format,
                    image=image_bytes_io,
                )
                image_objects.append(image_object)
        post_object = PostObject(
            None, None, None, None, None,
            post_db_object.message,
            PostState.posting.value,
            post_db_object.account_id,
            image_objects, None
        )
        for acc_obj in self.account_objects:
            if int(acc_obj.id) == int(post_object.account_id):
                break
        post_service = PostService('Facebook', acc_obj, post_object)
        post_errors = post_service.validate_prepare_post_data()
        if not post_errors:
            post_db_object.write({
                'state': PostState.posting.value
            })
            response_data = post_service.create_post_by_data()
            social_id: Optional[IdType] = response_data.get('id')
            post_db_object.write({
                'social_id': social_id,
                'state': PostState.posted.value,
                'posted_time': fields.Datetime.now(),
            }) if social_id else None
        else:
            post_db_object.write({
                'state': PostState.failed.value,
            })
            return post_errors

    # TODO: create massive deletion like massive creation
    def delete_old_posts_from_db(self) -> None:
        db_posts_ids: Dict[AccountType, List[IdType]] = self._get_accounts_and_related_posts()
        get_service = GetService(self.social_medias, self.account_objects)
        all_posts_ids_api = get_service.get_all_posts_ids_api()
        all_posts_ids_api_filtered = self._filter_non_connected_accounts(all_posts_ids_api)
        accounts_posts_ids = get_service.process_all_posts_ids(all_posts_ids_api_filtered)

        delete_service = DeleteService(self.social_medias, self.account_objects)
        delete_service.delete_several_posts(db_posts_ids, accounts_posts_ids)

    def delete_one_post_from_db(self, post_id: IdType) -> None:
        delete_service = DeleteService(self.social_medias, self.account_objects)
        delete_service.delete_one_post(post_id)

    def _get_accounts_and_related_posts(self) -> Dict[AccountType, List[IdType]]:
        accounts_with_posts: Dict[AccountType, List[IdType]] = dict()
        accounts = self._account_table.search([])
        for account in accounts:
            account_id = account.id
            posts = self._post_table.search([('account_id', '=', account_id)])
            post_ids = [post.social_id for post in posts]
            accounts_with_posts[account_id] = post_ids
        return accounts_with_posts

    def _process_image_data(self, image_data_bytes: bytes) -> Tuple[str, bytes]:
        image_data = io.BytesIO(image_data_bytes)
        image_format = Image.open(image_data).format.lower()

        image_data.seek(0)

        image = Image.open(image_data)
        image_bytes_io = io.BytesIO()
        image.save(image_bytes_io, image_format)
        image_bytes_io.seek(0)
        image.close()

        return image_format, image_bytes_io.read()
