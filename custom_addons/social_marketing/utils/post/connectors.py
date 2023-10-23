import json
import requests
from typing import (
    List,
)
from abc import (
    ABC,
    abstractmethod,
)
from ...custom_types import (
    ImageType,
    PostObject,
    IdType,
    PostType,
)
from ...custom_exceptions import (
    RequestException,
)
import facebook


class ConnectorInterface(ABC):
    @abstractmethod
    def create_post(self, post_data: PostType) -> PostType:
        pass

    @abstractmethod
    def flex_create_post(self) -> PostType:
        pass


GPAPH_API_VERSION = 'v17.0'


class FacebookConnector(ConnectorInterface):
    API_PREFIX = f'https://graph.facebook.com/{GPAPH_API_VERSION}'

    def __init__(self, page_id: IdType, access_token: str, account_id: IdType, post_object: PostObject = None) -> None:
        self._page_id = page_id
        self._access_token = access_token
        self.account_id = account_id
        self._post_object = post_object

    def create_post(self, post_data: PostType) -> PostType:
        url = f'{self.API_PREFIX}/{self._page_id}/feed'
        params = post_data
        params['access_token'] = self._access_token
        response = requests.post(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data

    def upload_image_to_facebook(self, image_data: ImageType) -> IdType:
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

    def flex_create_post(self) -> PostType:
        post_object = self._post_object
        image_objects = self._post_object.image_objects
        media_ids: List[IdType] = []

        for image_object in image_objects:
            media_id = self.upload_image_to_facebook({
                'source': (
                    f'{image_object.name}',
                    image_object.image,
                    f'image/{image_object.format}',
                ),
            })
            media_ids.append(media_id)

        if media_ids:
            attached_media = [{'media_fbid': media_id} for media_id in media_ids]
            response_data = self.create_post({
                'message': post_object.message if post_object.message else '',
                'published': True,
                'attached_media': str(attached_media),
            })
        else:
            response_data = self.create_post({
                'message': post_object.message if post_object.message else '',
                # 'attached_media': []
            })
        return response_data, media_ids