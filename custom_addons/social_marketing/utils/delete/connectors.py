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
    PostType,
    IdType,
)
from ...custom_exceptions import (
    RequestException,
)


class ConnectorInterface(ABC):
    @abstractmethod
    def delete_post(self, post_id: IdType) -> PostType:
        pass


GPAPH_API_VERSION = 'v17.0'

class FacebookConnector(ConnectorInterface):
    API_PREFIX = f'https://graph.facebook.com/{GPAPH_API_VERSION}'

    def __init__(self, page_id: str, access_token: str, account_id: IdType) -> None:
        self._page_id = page_id
        self._access_token = access_token
        self.account_id = account_id

    def delete_post(self, post_id: IdType) -> PostType:
        url = f'{self.API_PREFIX}/{post_id}'
        params = {
            'access_token': self._access_token,
        }
        response = requests.delete(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data
