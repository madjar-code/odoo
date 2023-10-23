import requests
import pytz
import io
import base64
from datetime import datetime
from PIL import Image
from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    List,
    Dict,
    Optional,
)
from pydantic import (
    AnyUrl,
)
from ...custom_types import (
    PostsListType,
    PostObject,
    PostState,
    IdType,
    ImageObject,
)


class PreparerInterface(ABC):
    @abstractmethod
    def transform_to_list_ids(
            self, posts_list_data: PostsListType) -> List[IdType]:
        pass

    @abstractmethod
    def process_all_posts_response(
            self, posts_list_data: PostsListType) -> List[PostObject]:
        pass


class FacebookPreparer(PreparerInterface):
    def transform_to_list_ids(
            self, posts_list_data: PostsListType) -> List[IdType]:
        all_posts_ids: List[IdType] = []

        for post_data in posts_list_data:
            all_posts_ids.append(post_data.get('id'))
        return all_posts_ids

    def process_all_posts_response(
            self, posts_list_data: PostsListType) -> List[PostObject]:
        all_posts: List[PostObject] = []
        for post_data in posts_list_data:
            attachments_objects = post_data.get('attachments')

            posted_time_str = post_data.get('created_time')
            if posted_time_str:
                posted_time = datetime.strptime(posted_time_str, '%Y-%m-%dT%H:%M:%S%z')
                posted_time_naive = posted_time.replace(tzinfo=None)
            else:
                posted_time_naive = None

            image_objects: List[ImageObject] = []
            if attachments_objects:
                attachments_data = attachments_objects['data']
                image_objects = self.process_attachments(attachments_data)

            message = post_data.get('message')

            shares_object = post_data.get('shares')
            likes_object = post_data.get('likes')
            comments_object = post_data.get('comments')
            
            posted_time = post_data.get('created_time')

            reposts_qty = self.process_shares(shares_object) if shares_object else None
            likes_qty = self.process_likes(likes_object) if likes_object else None
            comments_qty = self.process_comments(comments_object) if comments_object else None

            social_id = post_data['id']
            post_object = PostObject(
                social_id=social_id,
                reposts_qty=reposts_qty,
                likes_qty=likes_qty,
                views_qty=None,
                comments_qty=comments_qty,
                message=message,
                
                state=PostState.posted.value,
                account_id=None,
                image_objects=image_objects,
                posted_time=posted_time_naive,
            )
            all_posts.append(post_object)
        return all_posts

    def _process_image(self, image_url: AnyUrl, image_social_id: IdType) -> ImageObject:
        image_data_bytes = self._get_image_bytes(image_url)
        image_data = io.BytesIO(image_data_bytes)
        image_data_base64 = base64.b64encode(image_data.read()).decode('utf-8')
        image_data.seek(0)

        image = Image.open(io.BytesIO(image_data_bytes))
        image_format = image.format.lower()
        image.close()

        image_object = ImageObject(
            social_id=image_social_id,
            format=image_format,
            image=image_data_base64,
            name=None,
            description=None
        )
        return image_object

    def process_attachments(self, attachments: List[Dict]) -> List[ImageObject]:
        result_image_objects: List[ImageObject] = []
        for image in attachments:
            subattachments_objects = image.get('subattachments')
            if subattachments_objects:
                subattachments = subattachments_objects['data']
                for sub_image in subattachments:
                    image_url: AnyUrl = sub_image['media']['image']['src']
                    image_social_id: IdType = sub_image['target']['id']
                    image_object = self._process_image(image_url, image_social_id)
                    result_image_objects.append(image_object)
                return result_image_objects

            image_url: AnyUrl = image['media']['image']['src']
            image_social_id: IdType = image['target']['id']
            image_object = self._process_image(image_url, image_social_id)
            result_image_objects.append(image_object)
        return result_image_objects

    def _get_image_bytes(self, url: AnyUrl) -> Optional[bytes]:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                image_data = response.content
                return image_data
            else:
                return None
        except:
            return None

    def process_likes(self, likes_object: Dict) -> int:
        return likes_object['summary']['total_count']

    def process_shares(self, shares_object: Dict) -> int:
        return shares_object['count']

    def process_comments(self, comments_object: Dict) -> int:
        return comments_object['summary']['total_count']
