from typing import (
    List,
    Dict,
    Optional,
)
from ..custom_types import (
    SocialMediaType,
    AccountObject,
    PostsListType,
    AccountType,
    ErrorType,
    PostObject,
)
from ..custom_exceptions import (
    RequestException,
)
from .connectors import (
    ConnectorInterface,
    FacebookConnector,
)
from .preparers import (
    PreparerInterface,
    FacebookPreparer,
)


MEDIA_PREPARER = {'Facebook': FacebookPreparer,}
PREPARER_MEDIA = {FacebookPreparer: 'Facebook',}

MEDIA_CONNECTOR = {'Facebook': FacebookConnector,}
CONNECTOR_MEDIA = {FacebookConnector: 'Facebook',}


class GetService:
    def __init__(self, social_medias: List[SocialMediaType] = None,
                account_objects: List[AccountObject] = None) -> None:
        self.preparers: List[PreparerInterface] = []
        self.connectors: List[ConnectorInterface] = []

        for media in social_medias:
            preparer_class: Optional[PreparerInterface] = MEDIA_PREPARER.get(media)
            self.preparers.append(preparer_class()) if preparer_class else None

        for account in account_objects:
            connector_class: Optional[ConnectorInterface] = MEDIA_CONNECTOR.get(account.social_media)
            self.connectors.append(connector_class(**account.credentials,
                                                   account_id_name=account.id_name)
                                   ) if connector_class else None

    def get_all_posts_api(self) -> Dict[AccountType, PostsListType | ErrorType]:
        all_posts_api: Dict[AccountType, PostsListType] = dict()
        for connector in self.connectors:
            try:
                all_posts_api[connector.account_id_name] = connector.get_all_posts()
            except RequestException:
                all_posts_api[connector.account_id_name] = 'Problem with account connection'
        return all_posts_api

    def process_all_posts(self, all_posts_api: Dict[AccountType, PostsListType]
                          ) -> Dict[AccountType, List[PostObject]]:
        # PostListType --> List[PostObject]
        all_posts: Dict[AccountType, List[PostObject]] = dict()
        for preparer in self.preparers:
            for account, posts in all_posts_api.items():
                all_posts[account] = preparer.process_all_posts_response(posts)
        return all_posts
