from typing import Annotated
from fastapi import (
    APIRouter,
    Depends,
)
from odoo.api import Environment
# from odoo.addons.crm.models.crm_lead import Lead
from odoo.addons.fastapi.dependencies import odoo_env
from ..schemas import Lead


router = APIRouter(tags=['no_demo'])


@router.post('/crm_lead/create/')
async def create_lead(lead: Lead, env: Annotated[
        Environment, Depends(odoo_env)]) -> Lead:
    data = lead.model_dump(by_alias=True)
    crm_lead = env['crm.lead']
    crm_lead.sudo().create(data)
    return data
