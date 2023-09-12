import json
import requests
from abc import (
    ABC,
    abstractmethod,
)
from typing import List
from ...custom_types import(
    FieldName,
    PostsListType,
)
from ...custom_exceptions import (
    RequestException,
)


class ConnectorInterface(ABC):
    @abstractmethod
    def get_all_posts(self, fields: List[FieldName]) -> PostsListType:
        pass


GPAPH_API_VERSION = 'v17.0'

class FacebookConnector(ConnectorInterface):
    API_PREFIX = f'https://graph.facebook.com/{GPAPH_API_VERSION}'

    def __init__(self, page_id: str, access_token: str, account_id_name: str) -> None:
        self._page_id = page_id
        self._access_token = access_token
        self.account_id_name = account_id_name

    def get_all_posts(self, fields: List[FieldName] =\
            ['created_time', 'attachments', 'message', 'id',
             'count', 'likes.summary(true)', 'comments.summary(true)',
             'shares.summary(true)']) -> PostsListType:
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

