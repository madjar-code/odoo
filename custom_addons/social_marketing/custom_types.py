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
PostType: TypeAlias = Dict
CommentsListType: TypeAlias = List[Dict]
CommentType: TypeAlias = Dict
FieldErrorsType: TypeAlias = Dict[FieldName, List[str]]

# class PostType(str, Enum):
#     common = 'common'
#     single = 'single'


class Message(NamedTuple):
    success: bool
    field_name: FieldName
    text: str


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
    social_id: Optional[IdType]
    reposts_qty: Optional[int]
    likes_qty: Optional[int]
    views_qty: Optional[int]
    comments_qty: Optional[int]
    message: Optional[str]
    state: Optional[PostState]
    account_id: Optional[IdType]
    # account_id_name: Optional[IdType]
    # schedule_time: Optional[str]
    # type: Optional[PostType]
    # image_urls: List[AnyUrl]


class AccountObject(NamedTuple):
    id: IdType
    id_name: Optional[IdType]
    social_media: SocialMediaType
    credentials: Dict[str, str]
