import io
import base64
import json
import requests
from datetime import datetime
from PIL import Image
from abc import ABC, abstractmethod
from typing import (
    List,
    Dict,
    Optional,
)
from pydantic import AnyUrl
from ..custom_types import (
    IdType,
    Message,
    ImageType,
    ErrorType,
    PostState,
    PostType,
    FieldName,
    PostObject,
    ImageObject,
    PostsListType,
)
from ..custom_exceptions import RequestException


class PostServiceInterface(ABC):    
    @abstractmethod
    def get_post_list_ids(self) -> List[IdType]:
        pass

    @abstractmethod
    def validate_prepare_post_object(self, post_object: PostObject) ->\
            Dict[FieldName, List[ErrorType]]:
        pass

    @abstractmethod
    def get_post_list(self) -> List[PostObject]:
        pass

    @abstractmethod
    def create_post(self, post_object: PostObject) -> PostType:
        pass

    @abstractmethod
    def get_post(self, post_social_id: IdType) -> PostObject:
        pass

    @abstractmethod
    def update_post(self, post_object: PostObject) -> PostType:
        pass

    @abstractmethod
    def delete_post(self, post_id: IdType) -> PostType:
        pass

    @abstractmethod
    def create_image(self, image_object: ImageObject) -> ImageType:
        pass


LINKEDIN_API_VERSION = 'v2'
GPAPH_API_VERSION = 'v17.0'


class LinkedInPostService:
    API_PREFIX = f'https://api.linkedin.com/{LINKEDIN_API_VERSION}'
    TEXT_MAX_LENGTH = 8192
    
    def __init__(self, credentials: Dict[str, str]) -> None:
        self._account_urn = credentials['account_urn']
        self._access_token = credentials['access_token']

    def validate_prepare_post_object(self, post_object: PostObject) ->\
            Dict[FieldName, List[ErrorType]]:
        field_errors: Dict[FieldName, List[str]] = dict()
        if post_object.message:
            text_error = self._check_text(post_object.message)
            self._update_errors(text_error, field_errors)
        return field_errors

    def _check_text(self, text: str) -> Message:
        if len(text) > self.TEXT_MAX_LENGTH:
            return Message(
                success=False,
                field_name='message',
                text='Post text too long'
            )
        return Message(
            success=True,
            field_name='message',
            text='Post text is correct'
        )

    def _update_errors(
            self,
            message: Message,
            field_errors: Dict[FieldName, List[str]]
            ) -> None:
        if not message.success:
            if message.field_name not in field_errors:
                field_errors[message.field_name] = []
            field_errors[message.field_name].append(message.text)

    def create_post(self, post_object: PostObject) -> PostType:
        if post_object.image_objects:
            # TODO: handle image case
            pass
        else:
            response_data = self._create_post_api({
                'message': post_object.message if post_object.message else '',
            })
        return response_data

    def _create_post_api(self, post_data: PostType) -> PostType:
        url = f'{self.API_PREFIX}/ugcPosts/'
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json',
        }
        data = {
            'author': f'urn:li:{self._account_urn}',
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {
                        'text': post_data['message']
                    },
                    'shareMediaCategory': 'NONE'
                }
            },
            'visibility': {
                'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
            }
        }
        response = requests.post(
            url=url,
            headers=headers,
            json=data,  
        )
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data

    def delete_post(self, post_id: IdType) -> PostType:
        return self._delete_post_api(post_id)

    def _delete_post_api(self, post_id: IdType) -> PostType:
        url = f'{self.API_PREFIX}/ugcPosts/{post_id}'
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json',
        }
        response = requests.delete(url=url, headers=headers)
        return {'status': str(response.status_code)}


class FBPostService(PostServiceInterface):
    API_PREFIX = f'https://graph.facebook.com/{GPAPH_API_VERSION}'

    TEXT_MAX_LENGTH = 63602
    MAX_LINK_QTY = 5
    MIN_TIMEDELTA_SECS = 600

    def __init__(self, credentials: Dict[str, str]) -> None:
        self._page_id = credentials['page_id']
        self._access_token = credentials['access_token']

    def validate_prepare_post_object(self, post_object: PostObject) ->\
            Dict[FieldName, List[ErrorType]]:
        field_errors: Dict[FieldName, List[str]] = dict()
        if post_object.message:
            text_error = self._check_text(post_object.message)
            self._update_errors(text_error, field_errors)
        return field_errors

    def create_post(self, post_object: PostObject) -> PostType:
        if post_object.image_objects:
            attached_media = [{'media_fbid': image_object.social_id} \
                for image_object in post_object.image_objects]
            response_data = self._create_post_api({
                'message': post_object.message if post_object.message else '',
                'published': True,
                'attached_media': str(attached_media),
            })
        else:
            response_data = self._create_post_api({
                'message': post_object.message if post_object.message else '',
            })
        return response_data

    def _create_post_api(self, post_data: PostType) -> PostType:
        url = f'{self.API_PREFIX}/{self._page_id}/feed'
        params = post_data
        params['access_token'] = self._access_token
        response = requests.post(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data

    def _check_text(self, text: str) -> Message:
        if len(text) > self.TEXT_MAX_LENGTH:
            return Message(
                success=False,
                field_name='message',
                text='Post text too long'
            )
        return Message(
            success=True,
            field_name='message',
            text='Post text is correct'
        )

    def _update_errors(self, message: Message,
                       field_errors: Dict[FieldName, List[str]]) -> None:
        if not message.success:
            if message.field_name not in field_errors:
                field_errors[message.field_name] = []
            field_errors[message.field_name].append(message.text)

    def get_post(self, post_social_id: IdType) -> PostObject:
        post_data: PostType = self._get_post_api(post_social_id)
        return self._process_getting_post(post_data)

    def _get_post_api(
            self,
            post_social_id: IdType,
            fields: List[FieldName] = [
                'id',
                'message',
                'attachments',
                'created_time',
                'likes.summary(true)',
                'comments.summary(true)',
                'shares.summary(true)',
            ]) -> PostType:
        url = f'{self.API_PREFIX}/{post_social_id}'
        params = {
            'access_token': self._access_token,
            'fields': ','.join(fields),
        }
        response = requests.get(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(
                response_data['error']['message']
            )
        return response_data

    def _process_getting_post(self, post_data: PostType) -> PostObject:
        attachments_objects = post_data.get('attachments')
        image_objects: List[ImageObject] = []
        if attachments_objects:
            attachments_data = attachments_objects['data']
            image_objects = self._process_attachments(attachments_data)

        posted_time_str = post_data.get('created_time')
        posted_time = datetime.strptime(posted_time_str, '%Y-%m-%dT%H:%M:%S%z')
        posted_time_naive = posted_time.replace(tzinfo=None)

        message = post_data.get('message')

        shares_object = post_data.get('shares')
        likes_object = post_data.get('likes')
        comments_object = post_data.get('comments')

        posted_time = post_data.get('created_time')

        reposts_qty = self._process_shares(shares_object) if shares_object else None
        likes_qty = self._process_likes(likes_object) if likes_object else None
        comments_qty = self._process_comments(comments_object) if comments_object else None

        social_id = post_data['id']
        post_object = PostObject(
            social_id=social_id,
            reposts_qty=reposts_qty,
            likes_qty=likes_qty,
            views_qty=None,
            comments_qty=comments_qty,
            message=message,

            state=PostState.posted,
            account_id=None,
            image_objects=image_objects,
            posted_time=posted_time_naive,
        )
        return post_object

    def _process_attachments(self, attachments: List[Dict]) -> List[ImageObject]:
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

    def _get_image_bytes(self, url: AnyUrl) -> Optional[bytes]:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                image_data = response.content
                return image_data
        except:
            return None

    def _process_likes(self, likes_object: Dict) -> int:
        return likes_object['summary']['total_count']

    def _process_shares(self, shares_object: Dict) -> int:
        return shares_object['count']

    def _process_comments(self, comments_object: Dict) -> int:
        return comments_object['summary']['total_count']

    def get_post_list(self) -> List[PostObject]:
        post_list_api = self._get_post_list_api()
        return self._process_post_list_api(post_list_api)

    def _process_post_list_api(self, post_list_api: PostsListType) -> List[PostObject]:
        post_objects: List[PostObject] = list()
        for post_data in post_list_api:
            post_objects.append(self._process_getting_post(post_data))
        return post_objects

    def _get_post_list_api(
            self,
            fields: List[FieldName] = [
                'id',
                'count',
                'message',
                'attachments',
                'created_time',
                'likes.summary(true)',
                'comments.summary(true)',
                'shares.summary(true)',
            ]) -> PostsListType:
        url = f'{self.API_PREFIX}/{self._page_id}/feed'
        params = {
            'access_token': self._access_token,
            'fields': ','.join(fields),
        }
        response = requests.get(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data['data']

    def update_post(self, post_object: PostObject) -> PostType:
        media_ids: List[IdType] = []

        for image_object in post_object.image_objects:
            media_ids.append(image_object.social_id)

        attached_media = [{'media_fbid': media_id} for media_id in media_ids]
        response_data = self._update_post_api(
            post_object.social_id,
            post_data={
                'message': post_object.message if post_object.message else '',
                'published': True,
                'attached_media': str(attached_media),
            }
        )
        return response_data

    def _update_post_api(self, post_social_id: IdType,
            post_data: PostType) -> PostType:
        url = f'{self.API_PREFIX}/{post_social_id}'
        params = post_data
        params['access_token'] = self._access_token
        response = requests.post(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data

    def create_image(self, image_object: ImageObject) -> ImageType:
        media_id = self._upload_image_api({
            'source': (
                f'{image_object.name}',
                image_object.image,
                f'image/{image_object.format}',
            ),
        })
        return {'id': media_id}

    def _upload_image_api(self, image_data: ImageType) -> IdType:
        url = f'{self.API_PREFIX}/{self._page_id}/photos/'
        params = {
            'access_token': self._access_token,
            'published': False,
        }
        response = requests.post(url=url, params=params, files=image_data)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data.get('id')

    def delete_post(self, post_id: IdType) -> PostType:
        return self._delete_post_api(post_id)

    def _delete_post_api(self, post_id: IdType) -> PostType:
        url = f'{self.API_PREFIX}/{post_id}'
        params = {
            'access_token': self._access_token,
        }
        response = requests.delete(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data

    def get_post_list_ids(self) -> List[IdType]:
        post_list: PostsListType = self._get_post_list_api(fields=['id'])
        return self._transform_to_list_ids(post_list)

    def _transform_to_list_ids(self, post_list: PostsListType) -> List[IdType]:
        all_post_ids: List[IdType] = list()
        for post in post_list:
            all_post_ids.append(post.get('id'))
        return all_post_ids
