import requests
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
    ImageObject,
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
                 account_objects: List[AccountObject],
                 post_table, image_table) -> None:
        self.social_medias = social_medias
        self.account_objects = account_objects
        self._post_table = post_table
        self._image_table = image_table

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
        del post_dict['image_urls']
        post_dict['account_id'] = account_id
        new_post = self._post_table.create(post_dict)
        for image_url in post_object.image_urls:
            try:
                response = requests.get(image_url)
                response.raise_for_status()
                image_data = {
                    'name': image_url,
                    'description': '',
                    'image': response.content,
                    'post_id': new_post.id
                }
                self._image_table.create(image_data)
            except Exception as e:
                print(e)

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
        import io
        import requests
        import base64
        from PIL import Image

        # image_record = self._image_table.search([], limit=1)
        # image_data = io.BytesIO(base64.b64decode(image_record.image))
        # image_data.seek(0)

        # image_format = Image.open(image_data).format.lower()
        # image = Image.open(image_data)
        # image_bytes_io = io.BytesIO()
        # image.save(image_bytes_io, image_format)
        # image_bytes_io.seek(0)
        # image.close()

        # response = requests.post(
        #     f'https://graph.facebook.com/v17.0/{page_id}/photos/',
        #     params={
        #         'access_token': access_token
        #     },
        #     files={
        #         'source': (f'personal_image1.{image_format}', image_bytes_io.read(), f'image/{image_format}'),
        #         # 'source2': (f'personal_image2.{image_format}', image_bytes_io.read(), f'image/{image_format}'),
        #     }
        # )

        # print(f'\n\n{response.text}\n\n')

        non_existent_posts = self._post_table.search([
            ('social_id', '=', False)
        ])
        
        for post in non_existent_posts:
            related_images = self._image_table.search([
                ('post_id', '=', post.id)
            ])
            image_objects: List[ImageObject] = []

            for related_image in related_images:
                image_data = io.BytesIO(base64.b64decode(related_image.image))
                image_data.seek(0)

                image_format = Image.open(image_data).format.lower()
                image = Image.open(image_data)
                image_bytes_io = io.BytesIO()
                image.save(image_bytes_io, image_format)
                image_bytes_io.seek(0)
                image.close()

                print(f'\n\n{image_format}\n\n')
                image_object = ImageObject(
                    name=f'image.{image_format}',
                    description=None,
                    format=image_format,
                    image=image_bytes_io,
                )
                image_objects.append(image_object)

            post_object = PostObject(
                None,
                None,
                None,
                None,
                None,
                post.message,
                post.state,
                post.account_id,
                image_objects,
            )
            for acc_obj in self.account_objects:
                if acc_obj.id == post_object.account_id:
                    break
            post_service = PostService('Facebook', acc_obj, post_object=post_object)
            post_errors = post_service.validate_prepare_post_data()
            if not post_errors:
                response_data = post_service.create_post_by_data()
                # social_id: Optional[IdType] = response_data.get('id')
                # post.write({
                #     'social_id': social_id,
                # }) if social_id else None
            else:
                return post_errors
