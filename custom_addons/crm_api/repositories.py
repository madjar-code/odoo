from odoo.api import Environment
from pydantic import BaseModel


class OdooLeadFormRepository:
    def __init__(self, lead_table_name: str) -> None:
        self.lead_table_name = lead_table_name

    def create_validate_lead_form(self, lead_form_schema: BaseModel,
                                  form_table_name: str, env: Environment) -> None:
        lead_form_data = lead_form_schema.model_dump()
        form_table = env[form_table_name]
        crm_lead_table = env[self.lead_table_name]
        with env.cr.savepoint():
            lead_obj = crm_lead_table.sudo().create(
                lead_form_data['lead'])
            form_data = lead_form_data['form']
            form_data['lead_id'] = lead_obj.id
            form_table.sudo().create(form_data)
