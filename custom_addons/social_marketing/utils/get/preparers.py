from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    List,
    Dict,
)
from pydantic import (
    AnyUrl,
)
from ...custom_types import (
    PostsListType,
    PostObject,
    PostState,
)


class PreparerInterface(ABC):
    @abstractmethod
    def process_all_posts_response(
            self, posts_list_data: PostsListType) -> List[PostObject]:
        pass


class FacebookPreparer(PreparerInterface):
    def process_all_posts_response(
            self, posts_list_data: PostsListType) -> List[PostObject]:
        all_posts: List[PostObject] = []
        for post_data in posts_list_data:
            attachments_objects = post_data.get('attachments')
            image_urls = []
            if attachments_objects:
                attachments_data = attachments_objects['data']
                image_urls: List[AnyUrl] =\
                    self.process_attachments(attachments_data)
            message = post_data.get('message')

            shares_object = post_data.get('shares')
            likes_object = post_data.get('likes')
            comments_object = post_data.get('comments')

            reposts_qty = self.process_shares(shares_object) if shares_object else None
            likes_qty = self.process_likes(likes_object) if likes_object else None
            comments_qty = self.process_comments(comments_object) if comments_object else None

            social_id = post_data['id']
            post_object = PostObject(
                social_id=social_id,
                reposts_qty=reposts_qty,
                likes_qty=likes_qty,
                views_qty=None,
                comments_qty=comments_qty,
                message=message,
                state=PostState.posted.value,
                account_id=None,
                # image_urls=image_urls,
            )
            all_posts.append(post_object)
        return all_posts

    def process_attachments(self, attachments: Dict) -> List[AnyUrl]:
        return [image['media']['image']['src'] for image in attachments]

    def process_likes(self, likes_object: Dict) -> int:
        return likes_object['summary']['total_count']

    def process_shares(self, shares_object: Dict) -> int:
        return shares_object['count']

    def process_comments(self, comments_object: Dict) -> int:
        return comments_object['summary']['total_count']
