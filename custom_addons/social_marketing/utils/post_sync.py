import io
import base64
from PIL import Image
from typing import (
    Optional,
    Tuple,
    List,
    Dict,
    Any,
)
from odoo.models import fields
from odoo.exceptions import (
    UserError,
)
from .post_services import (
    PostServiceInterface,
    FBPostService,
    LinkedInPostService,
)
from ..models.accounts import Accounts
from ..custom_types import (
    FieldName,
    PostState,
    ImageObject,
    PostObject,
    IdType,
)


UPDATE_FIELDS = {
    'message': 'message',
    'reposts_qty': 'reposts_qty',
    'likes_qty': 'likes_qty',
    'comments_qty': 'comments_qty',
}


class PostRouter:
    def __init__(self, account_record: Accounts) -> None:
        self._account_record = account_record
        self._media_type = account_record.social_media

    @property
    def credentials(self) -> Dict[str, str]:
        acc = self._account_record
        if self._media_type == 'Facebook':
            return {
                'access_token': acc.fb_credentials_id.access_token,
                'page_id': acc.fb_credentials_id.page_id,
            }
        elif self._media_type == 'LinkedIn':
            return {
                'access_token': acc.li_credentials_id.access_token,
                'account_urn': acc.li_credentials_id.account_urn
            }

    @property
    def service(self) -> PostServiceInterface:
        if self._media_type == 'Facebook':
            return FBPostService(self.credentials)
        elif self._media_type == 'LinkedIn':
            return LinkedInPostService(self.credentials)


class PostSynchronizer:
    def __init__(self, env) -> None:
        self.env = env
        self._image_table = self.env['marketing.image']
        self._post_table = self.env['marketing.posts']
        self._group_table = self.env['marketing.stat.groups']

    def from_db_to_accounts(self, account_records) -> None:
        try:
            self.create_new_posts_db_to_acc()
            self.delete_old_posts_db_to_acc(account_records)
        except Exception as e:
            print(e)

    def create_new_posts_db_to_acc(self) -> None:
        non_existent_posts = self._post_table.search([
            ('social_id', '=', False)
        ])
        for post_record in non_existent_posts:
            self.create_one_post_db_to_acc(post_record)

    def delete_old_posts_db_to_acc(self, account_records) -> None:
        for account_record in account_records:
            service = PostRouter(account_record).service
            acc_post_ids = set(service.get_post_list_ids())
            db_post_ids = set(self._get_post_list_ids(account_record))
            post_ids_to_delete = acc_post_ids - db_post_ids
            for post_id in post_ids_to_delete:
                service.delete_post(post_id)

    def _get_post_list_ids(self, account_record) -> List[IdType]:
        account_id = account_record.id
        post_records = self._post_table.search([
            ('account_id', '=', account_id)
        ])
        return [post_record.social_id for post_record in post_records]

    def from_accounts_to_db(self, account_records) -> None:
        existing_social_ids: List[IdType] = self._get_all_social_ids()
        new_social_ids: List[IdType] = list()

        for account_record in account_records:
            service = PostRouter(account_record).service
            try:
                post_objects = service.get_post_list()
                for post_object in post_objects:
                    if post_object.social_id not in existing_social_ids:
                        self._create_non_existent_post(
                            post_object,
                            account_record.id
                        )
                    else:
                        self._update_existing_post(post_object)
                    new_social_ids.append(post_object.social_id)
            except Exception as e:
                print(e)
        # self._delete_non_existent_posts(existing_social_ids, new_social_ids)

    def _create_non_existent_post(self, post_object: PostObject,
                                  account_id: IdType) -> None:
        try:
            post_dict = post_object._asdict()
            del post_dict['image_objects']
            post_dict['account_id'] = account_id
            new_post = self._post_table.create(post_dict)
            for image_object in post_object.image_objects:
                image_data = {
                    'social_id': image_object.social_id,
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
            old_related_images_db = self._image_table.search([
                ('post_id', '=', existing_post.id)
            ]).read(['social_id'])
            old_social_image_ids = [_image.get('social_id') for _image in old_related_images_db]
            new_related_images = post_object.image_objects
            new_images_social_ids: List[IdType] = []
            for new_image in new_related_images:
                if new_image.social_id not in old_social_image_ids:
                    self._image_table.create({
                        'social_id': new_image.social_id,
                        'name': new_image.name,
                        'description': new_image.description,
                        'image': new_image.image,
                        'post_id': existing_post.id,
                    })
                new_images_social_ids.append(new_image.social_id)
            self._delete_non_existent_images(old_social_image_ids, new_images_social_ids)
        except Exception as e:
            print(e)

    def _delete_non_existent_posts(self, existing_social_ids: List[IdType],
                                  new_sociald_ids: List[IdType]) -> None:
        for old_social_id in existing_social_ids:
            if old_social_id not in new_sociald_ids:
                post_record_to_delete = self._post_table.search([
                    ('social_id', '=', old_social_id)
                ])
                if post_record_to_delete:
                    post_record_to_delete.unlink()

    def _get_all_social_ids(self) -> List[IdType]:
        posts = self._post_table.search_read([], ['social_id'])
        social_ids = [post['social_id'] for post in posts]
        return social_ids

    def create_one_post_db_to_acc(self, post_record) -> None:
        account_record = post_record.account_id
        service = PostRouter(account_record).service
        related_image_records = self._image_table.search([
            ('post_id', '=', post_record.id)
        ])
        image_objects = self._prepare_image_objects_list(
                service, related_image_records)
        post_object = PostObject(
            None, None, None, None, None,
            post_record.message,
            PostState.posting.value,
            post_record.account_id,
            image_objects, None
        )
        post_errors = service.validate_prepare_post_object(post_object)
        if not post_errors:
            if post_record.schedule_time and\
                    post_record.state == PostState.draft:
                post_record.write({
                    'state': PostState.scheduled
                })
                post_record.create_schedule_task()
            else:
                post_record.write({
                    'state': PostState.posting
                })
                response_data = service.create_post(post_object)
                social_id: Optional[IdType] = response_data.get('id')
                if social_id:
                    post_record.write({
                        'social_id': social_id,
                        'state': PostState.posted,
                        'posted_time': fields.Datetime.now(),
                    })
                else:
                    post_record.write({
                        'state': PostState.failed
                    })
        else:
            post_record.write({
                'state': PostState.failed,
            })
            raise UserError(str(post_errors))

    def update_one_post_db_to_acc(self, post_record) -> None:
        try:
            account_record = post_record.account_id
            service = PostRouter(account_record).service
            related_image_records = self._image_table.search([
                ('post_id', '=', post_record.id),
            ])
            image_objects = self._prepare_image_objects_list(
                service, related_image_records)
            post_record.write({
                'state': PostState.posting,
            })
            post_object = PostObject(
                post_record.social_id,
                None, None, None, None,
                post_record.message,
                PostState.posting,
                post_record.account_id,
                image_objects,
                None
            )
            response_data = service.update_post(post_object)
            if response_data.get('success'):
                post_record.write({
                    'state': PostState.posted,
                })
        except Exception as e:
            print(e)

    def _prepare_image_objects_list(
            self, service, related_image_records) -> List[ImageObject]:
        image_objects: List[ImageObject] = []
        for image_record in related_image_records:
            image_format, image_bytes_io = self._process_image_data(
                base64.b64decode(image_record.image)
            )
            image_object = ImageObject(
                name=f'image.{image_format}',
                social_id=image_record.social_id,
                description=None,
                format=image_format,
                image=image_bytes_io,
            )
            if not image_object.social_id:
                image_social_id = service.create_image(image_object).get('id')
                image_record.write({
                    'social_id': image_social_id,
                })
                image_object = ImageObject(
                    name=f'image.{image_format}',
                    social_id=image_social_id,
                    description=None,
                    format=image_format,
                    image=image_bytes_io,
                )
            image_objects.append(image_object)
        return image_objects

    def update_post_statistics(self, post_records) -> None:
        for post_record in post_records:
            account_record = post_record.account_id
            service = PostRouter(account_record).service
            try:
                post_object: PostObject = service.get_post(post_record.social_id)
            except Exception as e:
                print(e)
                continue
            self._update_post_statistics(post_object)

    def _update_post_statistics(self, post_object: PostObject) -> None:
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
        except Exception as e:
            print(e)

    def update_post_list_acc_to_db(self, post_list) -> None:
        for post_record in post_list:
            account_record = post_record.account_id
            service = PostRouter(account_record).service
            try:
                post_object: PostObject = service.get_post(post_record.social_id)
            except Exception as e:
                if 'Object does not exist' in str(e):
                    post_record.unlink()
                    continue
                print(e)
            self._update_post_record(post_object)

    def _update_post_record(self, post_object: PostObject) -> None:
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
            old_related_images_db = self._image_table.search(
                [('post_id', '=', existing_post.id)]
            ).read(['social_id'])
            old_social_image_ids = [_image.get('social_id') for _image in old_related_images_db]
            new_related_images = post_object.image_objects
            new_images_social_ids: List[IdType] = []

            for new_image in new_related_images:
                if new_image.social_id not in old_social_image_ids:
                    self._image_table.create({
                        'social_id': new_image.social_id,
                        'name': new_image.name,
                        'description': new_image.description,
                        'image': new_image.image,
                        'post_id': existing_post.id,
                    })
                new_images_social_ids.append(new_image.social_id)

            self._delete_non_existent_images(old_social_image_ids,
                                             new_images_social_ids)
        except Exception as e:
            print(e)

    def _delete_non_existent_images(self, old_social_image_ids: List[IdType],
                                    new_image_social_ids: List[IdType]) -> None:
        for old_social_id in old_social_image_ids:
            if old_social_id not in new_image_social_ids:
                image_to_delete = self._image_table.search([
                    ('social_id', '=', old_social_id)
                ])
                if image_to_delete:
                    image_to_delete.unlink()

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

    def delete_one_post_db_to_acc(self, post_record) -> None:
        service = PostRouter(post_record.account_id).service
        service.delete_post(post_record.social_id)
