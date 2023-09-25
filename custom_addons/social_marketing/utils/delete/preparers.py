import requests
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
    IdType,
)


class PreparerInterface(ABC):
    @abstractmethod
    def transform_to_list_ids(
            self, posts_list_data: PostsListType) -> List[IdType]:
        pass


class FacebookPreparer(PreparerInterface):
    def transform_to_list_ids(
            self, posts_list_data: PostsListType) -> List[IdType]:
        all_posts_ids: List[IdType] = []

        for post_data in posts_list_data:
            all_posts_ids.append(post_data.get('id'))
        return all_posts_ids
