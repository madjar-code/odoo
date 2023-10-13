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
    FBCommentService,
)


UPDATE_FIELDS = {
    'message': 'message',
}


class CommentDataSynchronizer:
    def __init__(self,
                 account_object: AccountObject,
                 post_social_id: IdType, post_id: IdType,
                 comment_table, post_table, lead_table = None) -> None:
        self._page_id = account_object.credentials['page_id']
        self._access_token = account_object.credentials['access_token']
        self.account_object = account_object
        self._post_social_id = post_social_id
        self._post_id = post_id

        self._comment_table = comment_table
        self._post_table = post_table
        self._lead_table = lead_table

    def comments_from_account_to_db(self) -> None:
        existing_social_ids: List[IdType] = self._get_all_social_ids()
        new_social_ids: List[IdType] = []

        comment_service = FBCommentService(self.account_object, 
                                           self._post_social_id,
                                           self._post_id)
        comment_objects: List[CommentObject] =\
            comment_service.get_comments_object_by_post_id()
        for comment_object in comment_objects:
            if comment_object.social_id not in existing_social_ids:
                self._comment_table.create(comment_object._asdict())
                print(comment_object._asdict())
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

    def _delete_non_existent_comments(self, existing_social_ids: List[IdType],
                                      new_social_ids: List[IdType]) -> None:
        for old_social_id in existing_social_ids:
            if old_social_id not in new_social_ids:
                comment_to_delete = self._comment_table.search([
                    ('social_id', '=', old_social_id)
                ])
                if comment_to_delete:
                    comment_to_delete.unlink()

    def comments_from_db_to_accounts(self) -> None:
        self._create_new_comments_from_db()
        self._update_old_comments_from_db()
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
            state=CommentState.posting.value,
            posted_time=None,
            parent_social_id=None,
        )
        comment_service = FBCommentService(self.account_object, 
                                           self._post_social_id,
                                           self._post_id, comment_object)
        comment_errors = comment_service.validate_prepare_comment_data()
        if not comment_errors:
            response_data = comment_service.create_comment_by_data()
            social_id: Optional[IdType] = response_data.get('id')
            comment_db_object.write({
                'social_id': social_id,
                'author_id': self.account_object.social_id,
                'state': CommentState.posted.value,
                'posted_time': fields.Datetime.now(),
            })
        else:
            comment_db_object.write({
                'state': CommentState.failed.value,
            })
            return comment_errors

    def _delete_old_comments_from_db(self) -> None:
        comment_service = FBCommentService(self.account_object, 
                                           self._post_social_id,
                                           self._post_id)
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
        comment_service = FBCommentService(self.account_object, 
                                           self._post_social_id,
                                           self._post_id)
        comment_objects_api: List[CommentObject] =\
            comment_service.get_comments_object_by_post_id()

        for comment_api in comment_objects_api:
            comment_db_query = self._comment_table.search(
                [('social_id', '=', comment_api.social_id),
                 ('author_id', '=', comment_api.author_id)]
            )
            if comment_db_query:
                comment_db = comment_db_query[0]
                comment_db = CommentObject(
                    social_id=comment_db.social_id,
                    message=comment_db.message,
                    author_id=comment_db.author_id,
                    post_id=comment_db.post_id,
                    parent_social_id=comment_db.parent_social_id,
                    posted_time=None,
                    state=None,
                )
                fields = self._compare_db_and_api_object(comment_db, comment_api)
                if fields:
                    update_service = FBCommentService(
                        self.account_object, 
                        self._post_social_id,
                        self._post_id,
                        comment_db
                    )
                    update_service.update_comment_by_data()    
                    # lead_records = self._lead_table.search([
                    #     ('name', 'ilike', str(comment_db.social_id))
                    # ])
                    # lead_records.write({
                    #     'description': f'Comment Message: {comment_db.message}'
                    # })

    def _compare_db_and_api_object(self,
                                   comment_db: CommentObject,
                                   comment_api: CommentObject) -> List[FieldName]:
        result_fields: List[FieldName] = []
        if comment_db.message != comment_api.message:
            result_fields.append(UPDATE_FIELDS['message'])
        return result_fields

    # def nested_comments_from_account_to_db(self, comment_social_id: IdType,
    #                                        comment_id: IdType) -> None:
    #     nested_comments: List[CommentObject] = FBCommentService(
    #         self.account_object, 
    #         self._post_social_id,
    #         self._post_id,
    #     ).get_comments_object_by_comment_id(comment_social_id)
    #     for comment_object in nested_comments:
    #         nested_comment_db_object =\
    #             self._comment_table.create(comment_object._asdict())
    #         nested_comment_db_object.write({
    #             'parent_id': comment_id,
    #         })
    #         print(f'\n\n{nested_comment_db_object}\n\n')
