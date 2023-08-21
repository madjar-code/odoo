from abc import ABC, abstractmethod
from odoo.api import Environment
from pydantic import BaseModel


class AbstractRepository(ABC):
    @abstractmethod
    def __init__(self, lead_table_name: str) -> None:
        """Save the lead_table_name value."""

    @abstractmethod
    def create_validate_lead_form(self, lead_form_schema: BaseModel,
                                  form_table_name: str, env: Environment) -> None:
        """Validate and create lead and form by schema."""


class OdooLeadFormRepository(AbstractRepository):
    def __init__(self, lead_table_name: str) -> None:
        self.lead_table_name = lead_table_name

    def create_validate_lead_form(self, lead_form_schema: BaseModel, env: Environment) -> None:
        lead_form_data = lead_form_schema.model_dump()
        # company_id, user_id = lead_form_data['lead']['company_id'],\
        #                       lead_form_data['lead']['user_id']
        # company_table, user_table = env['res.company'], env['res.users']

        # if company_id and not company_table.search([('id', '=', company_id)]):
        #     raise ValueError("Company with given id doesn't exist")

        # if user_id and not user_table.search([('id', '=', user_id)]):
        #     raise ValueError("User with given id doesn't exist")

        # form_table = env[form_table_name]

        crm_lead_table = env[self.lead_table_name]
        crm_property_value_table = env['crm.prop.value']
        crm_property_description_table = env['crm.prop.description']
        with env.cr.savepoint():
            lead_obj = crm_lead_table.sudo().create(
                lead_form_data['lead'])
            form_data = lead_form_data['form']
            for key, value in form_data.items():
                property_values = {
                    'name': key,
                    'type': 'char',
                    'value': value,
                    'lead_id': lead_obj.id,
                }
                prop_description = crm_property_description_table.sudo().search(
                    [('name', '=', property_values['name'])], limit=1)
                if prop_description:
                    crm_property_value_table.sudo().create({
                        'value': value,
                        'prop_description_id': prop_description[0].id,
                        'lead_id': lead_obj.id
                    })
                else:
                    prop_description = crm_property_description_table.sudo().create({
                        'name': property_values['name'],
                        'prop_type': property_values['type'],
                    })
                    crm_property_value_table.sudo().create({
                        'value': value,
                        'prop_description_id': prop_description.id,
                        'lead_id': lead_obj.id
                    })
            lead_obj.write({
                'type': 'lead',
            })


# class SQLLeadFormRepository(AbstractRepository):
#     def __init__(self, lead_table_name: str) -> None:
#         self.lead_table_name = lead_table_name.replace('.', '_')

#     def create_validate_lead_form(self, lead_form_schema: BaseModel,
#                                   form_table_name: str, env: Environment) -> None:
#         lead_form_data = lead_form_schema.dict()
#         lead_data = lead_form_data['lead']
#         form_data = lead_form_data['form']
#         form_table_name = form_table_name.replace('.', '_')

#         connection = psycopg2.connect(
#             database='',
#             user='',
#             password='',
#             host='',
#             port='',
#         )
        
#         with connection.cursor() as cursor:
#             lead_columns = ', '.join(lead_data.keys())
#             lead_values = ', '.join(['%s'] * len(lead_data))
#             lead_query = f'INSERT INTO {self.lead_table_name} ({lead_columns}) VALUES ({lead_values})'
#             cursor.execute(lead_query, tuple(lead_data.value()))
#             lead_id = cursor.fetchone()[0]

#             form_data['lead_id'] = lead_id
#             form_columns = ', '.join(form_data.keys())
#             form_values = ', '.join(['%s'] * len(form_data))
#             form_query = f'INSERT INTO {form_table_name} ({form_columns}) VALUES ({form_values})'
#             cursor.execute(form_query, tuple(form_data.values()))
