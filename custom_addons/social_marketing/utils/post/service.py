from typing import (
    List,
    Dict,
    Optional,
)
from ...custom_types import (
    SocialMediaType,
    AccountObject,
    FieldName,
    ErrorType,
    PostObject,
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


class PostService:
    def __init__(self, social_media: SocialMediaType,
                 account_object: AccountObject,
                 post_object: PostObject) -> None:
        self.preparer: Optional[PreparerInterface] = None
        self.connector: Optional[ConnectorInterface] = None

        preparer_class: Optional[PreparerInterface] = MEDIA_PREPARER.get(social_media)
        self.preparer = preparer_class(post_object) if preparer_class else None

        connector_class: Optional[ConnectorInterface] = MEDIA_CONNECTOR.get(account_object.social_media)
        self.connector = connector_class(**account_object.credentials,
                                         account_id=account_object.id,
                                         post_object=post_object)\
                                        if connector_class else None

    def validate_prepare_post_data(self) -> Dict[FieldName, List[ErrorType]]:
        return self.preparer.analyze_post_data()

    def create_post_by_data(self):
        try:
            return self.connector.flex_create_post()
        except RequestException:
            return {'error': 'Problem with account connection'}
