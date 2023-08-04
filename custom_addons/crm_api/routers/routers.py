from typing import (
    Annotated,
)
from fastapi import (
    APIRouter,
    Depends,
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

API_PREFIX = '/crm-lead'

router = APIRouter(tags=['crm_lead'])


def create_validate_lead_form(lead_form_schema, form_table, env):
    lead_form_data = lead_form_schema.model_dump(by_alias=True)
    crm_lead = env['crm.lead']
    with env.cr.savepoint():
        lead_obj = crm_lead.sudo().create(lead_form_data['lead'])
        form_data = lead_form_data['form']
        form_data['lead_id'] = lead_obj.id
        form_table.sudo().create(form_data)
    return {'message': 'OK!'}


@router.post(f'{API_PREFIX}/stepone-form/')
async def create_lead_stepone(
        lead_form: LeadSteponeFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    form_table = env['stepone.form']
    return create_validate_lead_form(lead_form, form_table, env)


@router.post(f'{API_PREFIX}/question-form/')
async def create_lead_question(
        lead_form: LeadQuestionFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    form_table = env['question.form']
    return create_validate_lead_form(lead_form, form_table, env)


@router.post(f'{API_PREFIX}/instant-form/')
async def create_lead_instant(
        lead_form: LeadInstantFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    form_table = env['instant.form']
    return create_validate_lead_form(lead_form, form_table, env)


@router.post(f'{API_PREFIX}/review-form/')
async def create_lead_review(
        lead_form: LeadReviewFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    form_table = env['review.form']
    return create_validate_lead_form(lead_form, form_table, env)


@router.post(f'{API_PREFIX}/request-quote-form/')
async def create_lead_request_quote(
        lead_form: LeadRequestQuoteFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    form_table = env['request.quote.form']
    return create_validate_lead_form(lead_form, form_table, env)


@router.post(f'{API_PREFIX}/default-form/')
async def create_lead_default(
        lead_form: LeadDefaultContactFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    form_table = env['default.form']
    return create_validate_lead_form(lead_form, form_table, env)
