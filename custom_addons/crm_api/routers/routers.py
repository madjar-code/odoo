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
from ..repositories import (
    OdooLeadFormRepository,
)


API_PREFIX = '/crm-lead'
router = APIRouter(tags=['crm_lead'])

lead_form_repo = OdooLeadFormRepository('crm.lead')


@router.post(f'{API_PREFIX}/stepone-form/')
async def create_lead_stepone(
        lead_form: LeadSteponeFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    lead_form_repo.create_validate_lead_form(lead_form, env)
    return {'message': 'stepone form was created!'}


@router.post(f'{API_PREFIX}/question-form/')
async def create_lead_question(
        lead_form: LeadQuestionFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    lead_form_repo.create_validate_lead_form(lead_form, env)
    return {'message': 'question form was created!'}


@router.post(f'{API_PREFIX}/instant-form/')
async def create_lead_instant(
        lead_form: LeadInstantFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    lead_form_repo.create_validate_lead_form(lead_form, env)
    return {'message': 'instant form was created!'}


@router.post(f'{API_PREFIX}/review-form/')
async def create_lead_review(
        lead_form: LeadReviewFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    lead_form_repo.create_validate_lead_form(lead_form, env)
    return {'message': 'review form was created!'}


@router.post(f'{API_PREFIX}/request-quote-form/')
async def create_lead_request_quote(
        lead_form: LeadRequestQuoteFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    lead_form_repo.create_validate_lead_form(lead_form, env)
    return {'message': 'request quote form was created!'}


@router.post(f'{API_PREFIX}/default-form/')
async def create_lead_default(
        lead_form: LeadDefaultContactFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    lead_form_repo.create_validate_lead_form(lead_form, env)
    return {'message': 'default form was created!'}
