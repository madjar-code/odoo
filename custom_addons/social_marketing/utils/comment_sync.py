from odoo import fields
from typing import (
    Optional,
    List,
    Dict,
    Any,
)
from ..custom_types import (
    AccountObject,
    CommentObject,
    CommentState,
    ErrorType,
    FieldName,
    IdType,
)
from ..utils.comment_services import (
    CommentServiceInterface,
    FBCommentService,
    InstCommentService,
)


UPDATE_FIELDS = {
    'message': 'message',
}


class CommentRouter:
    def __init__(
            self,
            account_object: AccountObject,
            post_social_id: IdType,
            post_id: IdType,
            comment_object: Optional[CommentObject] = None,
        ) -> None:
        self._account_object = account_object
        self._post_social_id = post_social_id
        self._post_id = post_id
        self._comment_object = comment_object
        self._media_type = account_object.social_media

    @property
    def service(self) -> CommentServiceInterface:
        if self._media_type == 'Facebook':
            return FBCommentService(
                self._account_object,
                self._post_social_id,
                self._post_id,
                self._comment_object,
            )
        elif self._media_type == 'Instagram':
            return InstCommentService(
                self._account_object,
                self._post_social_id,
                self._post_id,
                self._comment_object,
            )


class CommentSynchronizer:
    def __init__(
            self,
            account_object: AccountObject,
            post_social_id: IdType,
            post_id: IdType,
            env,
        ) -> None:
        self.account_object = account_object
        self._post_social_id = post_social_id
        self._post_id = post_id

        self.env = env
        self._comment_table = self.env['marketing.comment']
        self._post_table = self.env['marketing.posts']
        self._lead_table = self.env['crm.lead']

    def comments_from_account_to_db(self) -> None:
        existing_social_ids: List[IdType] = self._get_all_social_ids()
        new_social_ids: List[IdType] = list()

        comment_service: CommentServiceInterface =\
            CommentRouter(
                self.account_object,
                self._post_social_id,
                self._post_id,
            ).service
        comment_objects: List[CommentObject] =\
            comment_service.get_comments_object_by_post_id()
        for comment_object in comment_objects:
            if comment_object.social_id not in existing_social_ids:
                self._comment_table.create(comment_object._asdict())
            else:
                self._update_existing_comment(comment_object)
            new_social_ids.append(comment_object.social_id)
        self._delete_non_existent_comments(existing_social_ids, new_social_ids)

    def _get_all_social_ids(self) -> List[IdType]:
        comments = self._comment_table.search([('post_id', '=', self._post_id)])
        social_ids = [comment.social_id for comment in comments]
        return social_ids

    def _update_existing_comment(self, comment_object: CommentObject) -> None:
        try:
            existing_comment = self._comment_table.search([
                ('social_id', '=', comment_object.social_id)
            ])
            update_values: Dict[FieldName, Any] = {
                field_db: getattr(comment_object, field_db)
                for field_db, field_api in UPDATE_FIELDS.items()
                if getattr(existing_comment, field_db) != getattr(comment_object, field_api)
            }
            if update_values:
                existing_comment.write(update_values)
        except Exception as e:
            print(e)

    def _delete_non_existent_comments(
            self,
            existing_social_ids: List[IdType],
            new_social_ids: List[IdType]
        ) -> None:
        for old_social_id in existing_social_ids:
            if old_social_id not in new_social_ids:
                comment_to_delete = self._comment_table.search([
                    ('social_id', '=', old_social_id)
                ])
                if comment_to_delete:
                    comment_to_delete.unlink()

    def comments_from_db_to_accounts(self) -> None:
        self._create_new_comments_from_db()
        # self._update_old_comments_from_db()
        self._delete_old_comments_from_db()

    def _create_new_comments_from_db(self) -> None:
        non_existent_comments = self._comment_table.search([
            ('social_id', '=', False)
        ])
        for comment in non_existent_comments:
            self._create_one_comment_from_db(comment)

    def _create_one_comment_from_db(self, comment_db_object) ->\
            Optional[Dict[FieldName, List[ErrorType]]]:
        comment_object = CommentObject(
            social_id=None,
            message=comment_db_object.message,
            author_id=self.account_object.social_id,
            post_id=self._post_social_id,
            state=CommentState.posting,
            posted_time=None,
            parent_social_id=None,
        )
        comment_service: CommentServiceInterface =\
            CommentRouter(
                self.account_object,
                self._post_social_id,
                self._post_id,
                comment_object
            ).service
        comment_errors = comment_service.validate_prepare_comment_data()
        if not comment_errors:
            response_data = comment_service.create_comment_by_data()
            social_id: Optional[IdType] = response_data.get('id')
            comment_db_object.write({
                'social_id': social_id,
                'author_id': self.account_object.social_id,
                'state': CommentState.posted,
                'posted_time': fields.Datetime.now(),
            })
        else:
            comment_db_object.write({
                'state': CommentState.failed.value,
            })
            return comment_errors

    def _delete_old_comments_from_db(self) -> None:
        comment_service: CommentServiceInterface =\
            CommentRouter(
                self.account_object,
                self._post_social_id,
                self._post_id,
            ).service
        db_comment_ids = self._get_all_social_ids()
        api_comment_ids = comment_service.get_all_comments_ids_api()
        deleted_comment_ids = comment_service.delete_several_comments(
            db_comment_ids, api_comment_ids)
        for comment_id in deleted_comment_ids:
            lead_records = self._lead_table.search([
                ('name', 'ilike', str(comment_id))
            ])
            lead_records.unlink()

    def _update_old_comments_from_db(self) -> None:
        comment_service: CommentServiceInterface =\
            CommentRouter(
                self.account_object,
                self._post_social_id,
                self._post_id,
            ).service
        comment_objects_api: List[CommentObject] =\
            comment_service.get_comments_object_by_post_id()

        for comment_object in comment_objects_api:
            comment_db_query = self._comment_table.search(
                [('social_id', '=', comment_object.social_id),
                 ('author_id', '=', comment_object.author_id)]
            )
            if comment_db_query:
                comment_record = comment_db_query[0]
                comment_record = CommentObject(
                    social_id=comment_record.social_id,
                    message=comment_record.message,
                    author_id=comment_record.author_id,
                    post_id=comment_record.post_id,
                    parent_social_id=comment_record.parent_social_id,
                    posted_time=None,
                    state=None,
                )
                fields = self._compare_db_and_api_object(comment_record, comment_object)
                if fields:
                    update_service: CommentServiceInterface =\
                        CommentRouter(
                            self.account_object, 
                            self._post_social_id,
                            self._post_id,
                            comment_record,
                        ).service
                    update_service.update_comment_by_data()    

    def _compare_db_and_api_object(
            self,
            comment_record: CommentObject,
            comment_object: CommentObject
        ) -> List[FieldName]:
        result_fields: List[FieldName] = list()
        if comment_record.message != comment_object.message:
            result_fields.append(UPDATE_FIELDS['message'])
        return result_fields
