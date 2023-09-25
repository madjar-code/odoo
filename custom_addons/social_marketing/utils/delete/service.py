from typing import (
    List,
    Dict,
    Optional,
)
from ...custom_types import (
    SocialMediaType,
    AccountObject,
    PostsListType,
    AccountType,
    ErrorType,
    IdType,
)
from ...custom_exceptions import (
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


class DeleteService:
    def __init__(self, social_medias: List[SocialMediaType] = None,
                 account_objects: List[AccountObject] = None) -> None:
        self.connectors: List[ConnectorInterface] = []
        self.preparers: List[PreparerInterface] = []

        for media in social_medias:
            preparer_class: Optional[PreparerInterface] = MEDIA_PREPARER.get(media)
            self.preparers.append(preparer_class()) if preparer_class else None

        for account in account_objects:
            connector_class: Optional[ConnectorInterface] = MEDIA_CONNECTOR.get(account.social_media)
            self.connectors.append(connector_class(**account.credentials,
                                                   account_id=account.id)
                                   ) if connector_class else None

    def get_all_posts_api(self) -> Dict[AccountType, PostsListType | ErrorType]:
        all_posts_api: Dict[AccountType, PostsListType] = dict()
        for connector in self.connectors:
            try:
                all_posts_api[connector.account_id] = connector.get_all_posts_ids()
            except RequestException:
                all_posts_api[connector.account_id] = 'Problem with account connection'
        return all_posts_api

    def process_all_posts(self, all_posts_api: Dict[AccountType, PostsListType]
                          ) -> Dict[AccountType, List[IdType]]:
        all_posts_ids: Dict[AccountType, List[IdType]] = dict()
        for preparer in self.preparers:
            for account, posts in all_posts_api.items():
                all_posts_ids[account] = preparer.transform_to_list_ids(posts)
        return all_posts_ids

    def delete_post(self, connector: ConnectorInterface, 
                    post_social_id: IdType) -> None:
        try:
            connector.delete_post(post_social_id)
        except RequestException:
            return {'error': 'Problem with account_connection'}

    def delete_several_posts(self, db_posts_ids: Dict[AccountType, List[IdType]],
                             account_posts_ids: Dict[AccountType, List[IdType]]) -> None:
        for connector in self.connectors:
            db_ids = db_posts_ids[connector.account_id]
            account_ids = account_posts_ids[connector.account_id]
            delta_ids: List[IdType] = self._compare_two_id_list(db_ids, account_ids)
            if delta_ids:
                for post_id in delta_ids:
                    self.delete_post(connector, post_id)

    def _compare_two_id_list(self, db_posts_ids: List[IdType],
                             account_posts_ids: List[IdType]) -> List[IdType]:
        """return posts_ids from account that doesn't exist in db"""
        return [post_id for post_id in account_posts_ids if post_id not in db_posts_ids]
