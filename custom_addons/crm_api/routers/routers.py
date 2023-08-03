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
)


router = APIRouter(tags=['crm_lead'])


TABLE_MAPPING = {
    'SteponeForm': 'stepone.form',
    'QuestionForm': 'question.form',
}


@router.post('/crm_lead/stepone-form/')
async def create_lead(
        lead_form: LeadSteponeFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    try:
        form_table_name = TABLE_MAPPING['SteponeForm']
        form_table = env[form_table_name]
    except KeyError:
        raise HTTPException(status_code=403, detail='Incorrect form name')
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


@router.post('/crm_lead/question-form/')
async def create_lead(
        lead_form: LeadQuestionFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    try:
        form_table_name = TABLE_MAPPING['QuestionForm']
        form_table = env[form_table_name]
    except KeyError:
        raise HTTPException(status_code=403, detail='Incorrect form name')
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