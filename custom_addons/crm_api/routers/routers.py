from enum import Enum
from typing import Annotated
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from odoo.api import Environment
from odoo.addons.fastapi.dependencies import odoo_env
from ..schemas import (
    LeadSteponeFormSchema,
    LeadQuestionFormSchema,
    LeadInstantFormSchema,
    LeadReviewFormSchema,
    LeadRequestQuoteFormSchema,
    LeadDefaultContactFormSchema,
)


router = APIRouter(tags=['crm_lead'])


TABLE_MAPPING = {
    'SteponeForm': 'stepone.form',
    'QuestionForm': 'question.form',
    'InstantForm': 'instant.form',
    'ReviewForm': 'review.form',
    'RequestQuoteForm': 'request.quote.form',
    'DefaultContactForm': 'default.form',
}


def create_validate_lead_form(
        lead_form,
        table_key: str,
        env: Annotated[Environment, Depends(odoo_env)]
    ):
    try:
        form_table_name = TABLE_MAPPING[table_key]
        form_table = env[form_table_name]
    except KeyError:
        raise HTTPException(status_code=403, detail='Incorrect table name')
    lead_form_data = lead_form.model_dump(by_alias=True)
    crm_lead = env['crm.lead']
    try:
        with env.cr.savepoint():
            lead_obj = crm_lead.sudo().create(lead_form_data['lead'])
            form_data = lead_form_data['form']
            form_data['lead_id'] = lead_obj.id
            form_table.sudo().create(form_data)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=422, detail='Something went wrong')
    return {'message': 'OK!'}


@router.post('/crm_lead/stepone-form/')
async def create_lead(
        lead_form: LeadSteponeFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    return create_validate_lead_form(lead_form, 'SteponeForm', env)


@router.post('/crm_lead/question-form/')
async def create_lead(
        lead_form: LeadQuestionFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    return create_validate_lead_form(lead_form, 'QuestionForm', env)


@router.post('/crm_lead/instant-form/')
async def create_lead(
        lead_form: LeadInstantFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    return create_validate_lead_form(lead_form, 'InstantForm', env)


@router.post('/crm_lead/review-form/')
async def create_lead(
        lead_form: LeadReviewFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    return create_validate_lead_form(lead_form, 'ReviewForm', env)


@router.post('/crm_lead/request-quote-form/')
async def create_lead(
        lead_form: LeadRequestQuoteFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    return create_validate_lead_form(lead_form, 'RequestQuoteForm', env)

@router.post('/crm_lead/default-form/')
async def create_lead(
        lead_form: LeadDefaultContactFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    return create_validate_lead_form(lead_form, 'DefaultContactForm', env)
