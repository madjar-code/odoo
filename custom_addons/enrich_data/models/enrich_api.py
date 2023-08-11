from typing import Dict
from pydantic import EmailStr
# from odoo import models, api
from ..utils.representor import (
    get_data_from_website,
    process_website_data,    
)


class IncorrectEmailError(Exception):
    """Raises if email is incorrect."""


class EnrichAPI:
    # _name = 'enrich.api'
    # _description = 'Lead Enrichment API'

    # @api.model
    def _request_enrich(self, lead_emails: Dict[int, EmailStr]) -> Dict:
        result_data = dict()
        for lead_id, lead_email in lead_emails.items():
            at_index = lead_email.find('@')
            if at_index == -1:
                raise IncorrectEmailError()
            domain = lead_email[at_index + 1:]
            home_url = 'https://' + domain
            url_prefix = home_url

            website_data = get_data_from_website(url_prefix, home_url)
            result_data[lead_id] = process_website_data(website_data)

        return result_data
