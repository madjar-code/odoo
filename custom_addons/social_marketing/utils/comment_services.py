import json
import requests
from datetime import datetime
from abc import ABC, abstractmethod
from typing import (
    List,
    Dict,
    Optional,
)
from ..custom_exceptions import\
    RequestException
from ..custom_types import (
    CommentObject,
    CommentState,
    AccountObject,
    CommentListType,
    CommentType,
    FieldName,
    ErrorType,
    IdType,
)

class CommentServiceInterface(ABC):
    @abstractmethod
    def get_all_comments_ids_api(self) -> List[IdType]:
        pass

    @abstractmethod
    def get_comments_object_by_post_id(self) -> List[CommentObject]:
        pass

    @abstractmethod
    def get_comments_object_by_comment_id(
            self, comment_id: IdType) -> List[CommentObject]:
        pass

    @abstractmethod
    def create_comment_by_data(self) -> CommentType:
        pass

    @abstractmethod
    def validate_prepare_comment_data(self) -> Dict[FieldName, List[ErrorType]]:
        pass

    @abstractmethod
    def update_comment_by_data(self) -> CommentType:
        pass

    @abstractmethod
    def delete_several_comments(
            self,
            db_comment_ids: List[IdType],
            api_comment_ids: List[IdType]
        ) -> List[IdType]:
        pass


GRAPH_API_VERSION = 'v17.0'


class InstCommentService(CommentServiceInterface):
    API_PREFIX = f'https://graph.facebook.com/{GRAPH_API_VERSION}'

    def __init__(
            self,
            account_object: AccountObject,
            post_social_id: IdType,
            post_id: IdType,
            comment_object: Optional[CommentObject] = None
        ) -> None:
        self._page_id = account_object.credentials['page_id']
        self._access_token = account_object.credentials['access_token']
        self._post_social_id = post_social_id
        self._post_id = post_id
        self.comment_object = comment_object

    def get_all_comments_ids_api(self) -> List[IdType]:
        result_id_list: List[IdType] = []
        comment_object_list: CommentListType =\
            self._get_comments_by_post_id_api(fields=['id'])
        # print(f'\n{comment_object_list}\n')
        for comment_object in comment_object_list:
            result_id_list.append(comment_object.get('id'))
        return result_id_list

    def get_comments_object_by_post_id(self) -> List[CommentObject]:
        comment_list_data: CommentListType = self._get_comments_by_post_id_api()
        return self._process_getting_comments(comment_list_data)

    def _get_comments_by_post_id_api(
            self, 
            fields: List[FieldName] = [
                'id',
                'text',
                'like_count',
                'timestamp',
                'user',
                'from',
            ]) -> CommentListType:
        url = f'{self.API_PREFIX}/{self._post_social_id}'
        params = {
            'access_token': self._access_token,
            'fields': f'comments_count,comments{{{",".join(fields)}}}',
        }
        response = requests.get(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        if response_data.get('comments'):
            return response_data.get('comments').get('data')
        return list()

    def _process_getting_comments(
            self,
            comment_list_data: CommentListType
        ) -> List[CommentObject]:
        all_comments: List[CommentObject] = list()
        for comment_data in comment_list_data:
            message = comment_data.get('text')
            social_id = comment_data.get('id')
            author_id = comment_data.get('from').get('id')
            post_id = self._post_id

            posted_time_str = comment_data.get('timestamp')
            if posted_time_str:
                posted_time = datetime.strptime(posted_time_str, '%Y-%m-%dT%H:%M:%S%z')
                posted_time_naive = posted_time.replace(tzinfo=None)
            else:
                posted_time_naive = None

            parent_id = comment_data.get('parent')
            if parent_id:
                parent_id = parent_id.get('id')

            comment_object = CommentObject(
                social_id=social_id,
                message=message,
                author_id=author_id,
                post_id=post_id,
                posted_time=posted_time_naive,
                state=CommentState.posted,
                parent_social_id=parent_id,
            )
            all_comments.append(comment_object)
        return all_comments

    def get_comments_object_by_comment_id(
            self, comment_id: IdType) -> List[CommentObject]:
        return super().get_comments_object_by_comment_id(comment_id)

    def create_comment_by_data(self) -> CommentType:
        try:
            return self._create_comment_api()
        except RequestException as e:
            return {'error': str(e)}

    def _create_comment_api(self) -> CommentType:
        comment_object = self.comment_object
        if comment_object:
            url = f'{self.API_PREFIX}/{self._post_social_id}/comments'
            params = {
                'access_token': self._access_token,
                'message': comment_object.message,
            }
            response = requests.post(url=url, params=params)
            response_data = json.loads(response.text)
            if response_data.get('error'):
                raise RequestException(response_data['error']['message'])
            return response_data

    def validate_prepare_comment_data(self) -> Dict[FieldName, List[ErrorType]]:
        errors = dict()        
        comment = self.comment_object
        if comment:
            if not comment.message:
                errors['message'] = 'Field may not be blank'
        return errors

    def update_comment_by_data(self) -> CommentType:
        try:
            return self._update_comment_api()
        except RequestException as e:
            return {'error': str(e)}

    def _update_comment_api(self) -> CommentType:
        comment_object = self.comment_object
        if comment_object:
            url = f'https://graph.instagram.com/v12.0/{comment_object.social_id}'
            params = {
                'access_token': self._access_token,
                'message': comment_object.message,
            }
            response = requests.post(url=url, params=params)
            response_data = json.loads(response.text)
            if response_data.get('error'):
                raise RequestException(response_data['error']['message'])
            return response_data

    def delete_several_comments(
            self,
            db_comment_ids: List[IdType],
            api_comment_ids: List[IdType]
        ) -> List[IdType]:
        delta_ids: List[IdType] = self._compare_two_id_list(
            db_comment_ids,
            api_comment_ids
        )
        for comment_id in delta_ids:
            try:
                self._delete_post_api(comment_id)
            except RequestException as e:
                return {'error': str(e)}
        return delta_ids

    def _delete_post_api(self, comment_id: IdType) -> CommentType:
        url = f'{self.API_PREFIX}/{comment_id}'
        params = {
            'access_token': self._access_token,
        }
        response = requests.delete(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data

    def _compare_two_id_list(
            self,
            db_comment_ids: List[IdType],
            api_comment_ids: List[IdType]
        ) -> List[IdType]:
        return [
            comment_id for comment_id in api_comment_ids\
                if comment_id not in db_comment_ids
        ]


class FBCommentService(CommentServiceInterface):
    API_PREFIX = f'https://graph.facebook.com/{GRAPH_API_VERSION}'

    def __init__(
            self,
            account_object: AccountObject,
            post_social_id: IdType,
            post_id: IdType,
            comment_object: Optional[CommentObject] = None
        ) -> None:
        self._page_id = account_object.credentials['page_id']
        self._access_token = account_object.credentials['access_token']
        self._post_social_id = post_social_id
        self._post_id = post_id
        self.comment_object = comment_object

    def _get_comments_by_post_id_api(
            self, 
            fields: List[FieldName] = [
                'id',
                'message',
                'like_count',
                'created_time',
                'from',
            ]) -> CommentListType:
        url = f'{self.API_PREFIX}/{self._post_social_id}/comments'
        params = {
            'access_token': self._access_token,
            'fields': ','.join(fields),
        }
        response = requests.get(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data['data']

    def _get_comments_recursive(
            self,
            comment_id: IdType,
            all_comments: CommentListType,
            fields: List[FieldName] = [
                'id',
                'message',
                'like_count', 
                'created_time',
                'from',
                'parent{id}'
            ]) -> None:
        url = f'{self.API_PREFIX}/{comment_id}/comments'
        params = {
            'access_token': self._access_token,
            'fields': ','.join(fields),
        }
        response = requests.get(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        all_comments += response_data['data']

    def get_all_comments_ids_api(self) -> List[IdType]:
        result_id_list: List[IdType] = []
        comment_object_list: CommentListType =\
            self._get_comments_by_post_id_api(fields=['id', 'from'])
        for comment_object in comment_object_list:
            result_id_list.append(comment_object.get('id'))
        return result_id_list

    def _process_getting_comments(self, comment_list_data:\
            CommentListType) -> List[CommentObject]:
        all_comments: List[CommentObject] = []
        for comment_data in comment_list_data:
            message = comment_data.get('message')
            social_id = comment_data.get('id')
            author_id = comment_data.get('from').get('id')
            post_id = self._post_id

            posted_time_str = comment_data.get('created_time')
            if posted_time_str:
                posted_time = datetime.strptime(posted_time_str, '%Y-%m-%dT%H:%M:%S%z')
                posted_time_naive = posted_time.replace(tzinfo=None)
            else:
                posted_time_naive = None

            parent_id = comment_data.get('parent')
            if parent_id:
                parent_id = parent_id.get('id')

            comment_object = CommentObject(
                social_id=social_id,
                message=message,
                author_id=author_id,
                post_id=post_id,
                posted_time=posted_time_naive,
                state=CommentState.posted.value,
                parent_social_id=parent_id,
            )
            all_comments.append(comment_object)
        return all_comments

    def get_comments_object_by_post_id(self) -> List[CommentObject]:
        comment_list_data: CommentListType = self._get_comments_by_post_id_api()
        return self._process_getting_comments(comment_list_data)

    def get_comments_object_by_comment_id(
            self, comment_id: IdType) -> List[CommentObject]:
        comment_list_data: CommentListType = []
        self._get_comments_recursive(comment_id, comment_list_data)
        return self._process_getting_comments(comment_list_data)
 
    def validate_prepare_comment_data(self) -> Dict[FieldName, List[ErrorType]]:
        errors = dict()        
        comment = self.comment_object
        if comment:
            if not comment.message:
                errors['message'] = 'Field may not be blank'
        return errors

    def create_comment_by_data(self) -> CommentType:
        try:
            return self._create_comment_api()
        except RequestException as e:
            return {'error': str(e)}

    def _create_comment_api(self) -> CommentType:
        comment = self.comment_object
        if comment:
            url = f'{self.API_PREFIX}/{self._post_social_id}/comments'
            params = {
                'access_token': self._access_token,
                'message': comment.message,
            }
            response = requests.post(url=url, params=params)
            response_data = json.loads(response.text)
            if response_data.get('error'):
                raise RequestException(response_data['error']['message'])
            return response_data

    def update_comment_by_data(self) -> CommentType:
        try:
            return self._update_comment_api()
        except RequestException as e:
            return {'error': str(e)}

    def _update_comment_api(self) -> CommentType:
        comment = self.comment_object
        if comment:
            url = f'{self.API_PREFIX}/{comment.social_id}'
            params = {
                'access_token': self._access_token,
                'message': comment.message,
            }
            response = requests.post(url=url, params=params)
            response_data = json.loads(response.text)
            if response_data.get('error'):
                raise RequestException(response_data['error']['message'])
            return response_data

    def delete_several_comments(
            self,
            db_comment_ids: List[IdType],
            api_comment_ids: List[IdType]
        ) -> List[IdType]:
        delta_ids: List[IdType] = self._compare_two_id_list(
            db_comment_ids,
            api_comment_ids
        )
        for comment_id in delta_ids:
            try:
                self._delete_post_api(comment_id)
            except RequestException as e:
                return {'error': str(e)}
        return delta_ids

    def _delete_post_api(self, comment_id: IdType) -> CommentType:
        url = f'{self.API_PREFIX}/{comment_id}'
        params = {
            'access_token': self._access_token,
        }
        response = requests.delete(url=url, params=params)
        response_data = json.loads(response.text)
        if response_data.get('error'):
            raise RequestException(response_data['error']['message'])
        return response_data

    def _compare_two_id_list(
            self,
            db_comment_ids: List[IdType],
            api_comment_ids: List[IdType]
        ) -> List[IdType]:
        return [
            comment_id for comment_id in api_comment_ids\
                if comment_id not in db_comment_ids
        ]
