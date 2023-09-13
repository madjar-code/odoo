import json
import requests
from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Optional,
)
from ...custom_types import (
    ErrorType,
    PostObject,
    IdType,
    PostType,
    CommentType,
)
from ...custom_exceptions import (
    RequestException,
)


class ConnectorInterface(ABC):
    @abstractmethod
    def create_post(self, post_data: PostType) -> PostType:
        pass

    @abstractmethod
    def create_comment_on_post(self, post_id: IdType) -> CommentType:
        pass

    @abstractmethod
    def flex_create_post(self) -> PostType:
        pass


GPAPH_API_VERSION = 'v17.0'

class FacebookConnector(ConnectorInterface):
    API_PREFIX = f'https://graph.facebook.com/{GPAPH_API_VERSION}'

    def __init__(self, page_id: IdType, access_token: str,
                 account_id: IdType, post_object: PostObject = None) -> None:
        self._page_id = page_id
        self._access_token = access_token
        self.account_id = account_id
        self._post_object = post_object

    def create_post(self, post_data: PostType) -> PostType:
        """
        Can be used for:
        - scheduled post;
        - post with link;
        - post only with text;
        """
        url = f'{self.API_PREFIX}/{self._page_id}/feed'
        params = post_data
        params['access_token'] = self._access_token
        response = requests.post(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data

    def create_post_with_images(self, post_data: PostType) -> PostType:
        url = f'{self.API_PREFIX}/{self._page_id}/photos/'
        params = post_data
        params['access_token'] = self._access_token
        response = requests.post(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data

    def create_comment_on_post(
            self, post_id: IdType, comment_data: CommentType) -> CommentType:
        url = f'{self.API_PREFIX}/{post_id}/comments/'
        params = comment_data
        params['access_token'] = self._access_token
        response = requests.post(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data

    def flex_create_post(self) -> PostType:
        post_data = self._post_object
        # if post_data.attach_images:
        #     response_data = self.create_post_with_images(
        #         {
        #             'message': post_data.message,
        #             'url': post_data.attach_images,
        #         }
            # )
        # elif post_data.schedule_time:
        #     response_data = self.create_post(
        #         {
        #             'message': post_data.schedule_time,
        #             'published': 'false',
        #             'scheduled_publishing_time': post_data.schedule_time,
        #         }
        #     )
        if post_data:
            response_data = self.create_post(
                {
                    'message': post_data.message,
                }
            )
        return response_data
