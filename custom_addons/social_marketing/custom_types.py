from enum import Enum
from typing import (
    TypeAlias,
    NamedTuple,
    List,
    Dict,
    Optional,
)

AccountType: TypeAlias = str
TimestampType: TypeAlias = str
FieldName: TypeAlias = str
IdType: TypeAlias = int
ErrorType: TypeAlias = str
PostsListType: TypeAlias = List[Dict]
FieldErrorsType: TypeAlias = Dict[FieldName, List[str]]


# class PostType(str, Enum):
#     common = 'common'
#     single = 'single'


class PostState(str, Enum):
    draft = 'draft'
    scheduled = 'scheduled'
    posting = 'posting'
    posted = 'posted'


class SocialMediaType(str, Enum):
    facebook = 'Facebook'
    linkedin = 'LinkedIn'
    instagram = 'Instagram'
    youtube = 'Youtube'
    twitter = 'Twitter'


class PostObject(NamedTuple):
    social_id: IdType
    reposts_qty: Optional[int]
    likes_qty: Optional[int]
    views_qty: Optional[int]
    comments_qty: Optional[int]
    message: Optional[str]
    state: Optional[PostState]
    # type: Optional[PostType]
    # image_urls: List[AnyUrl]


class AccountObject(NamedTuple):
    id_name: str
    social_media: SocialMediaType
    credentials: Dict[str, str]
