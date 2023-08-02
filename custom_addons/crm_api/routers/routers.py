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
    LeadFormSchema,
)


router = APIRouter(tags=['crm_lead'])


TABLE_MAPPING = {
    'SteponeForm': 'stepone.form',
}


@router.post('/crm_lead/{form_name}/')
async def create_lead(
        form_name: str,
        lead_form: LeadFormSchema,
        env: Annotated[Environment, Depends(odoo_env)],
    ):
    try:
        form_table_name = TABLE_MAPPING[form_name]
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
