import os
import uuid
import shutil
from typing import (
    Annotated,
)
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
)
from odoo.api import Environment
from odoo.addons.fastapi.dependencies import odoo_env
from ...stepone.schemas.forms import SteponeForm
from ..schemas import (
    LeadSchema,
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
        env: Annotated[Environment, Depends(odoo_env)],
        lead: LeadSchema = Depends(),
        form: SteponeForm = Depends(),
        file: UploadFile = File(...),
    ):
    unique_dir_name = str(uuid.uuid4())
    upload_dir = os.path.join(os.getcwd(), f'uploads/{unique_dir_name}')

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    dest = os.path.join(upload_dir, file.filename)

    with open(dest, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)

    DIR_PREFIX = 'http://localhost:8069/uploads'
    ALLOWED_FORMATS = (
        '.doc',
        '.docx',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.pdf',
    )

    _, file_format = os.path.splitext(file.filename)
    
    if file_format not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail='Incorrect file format')

    file_size = file.file.tell()
    
    TOP_SIZE = 20 * 1024 * 1024  # 20 MB
    if file_size > TOP_SIZE:
        raise HTTPException(status_code=400, detail='File is too big')

    form.file = f'{DIR_PREFIX}/{unique_dir_name}/{file.filename}'
    lead_form_data = {
        'lead': lead.model_dump(),
        'form': form.model_dump(),
    }
    lead_form = LeadSteponeFormSchema(**lead_form_data)
    lead_form_repo.create_validate_lead_form(lead_form, env)
    return {'message': 'stepone form was created!'}


@router.post(f'{API_PREFIX}/question-form/')
async def create_lead_question(
        lead_form: LeadQuestionFormSchema ,
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
