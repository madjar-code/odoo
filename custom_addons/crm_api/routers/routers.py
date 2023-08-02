from typing import Annotated
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Body,
)
from fastapi.openapi.models import Example
from odoo.api import Environment
# from odoo.addons.crm.models.crm_lead import Lead
from odoo.addons.fastapi.dependencies import odoo_env
from ..schemas import (
    Lead,
    LeadFormSchema
)


router = APIRouter(tags=['crm_lead'])


@router.post('/crm_lead/{form_name}/')
async def create_lead(
        form_name: str,
        lead_form: LeadFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    lead_form_data = lead_form.model_dump(by_alias=True)
    crm_lead = env['crm.lead']
    stepone_form = env['stepone.form']
    try:
        with env.cr.savepoint():    
            lead_obj = crm_lead.sudo().create(lead_form_data['lead'])
            form_data = lead_form_data['form']
            form_data['lead_id'] = lead_obj.id
            stepone_form.sudo().create(form_data)
    except Exception as e:
        error_messages = 'Something went wrong'
        raise HTTPException(status_code=422, detail=error_messages)
    return {'message': 'OK!'}
