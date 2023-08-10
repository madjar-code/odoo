from pydantic import EmailStr
from odoo import models, api
from ..utils.representor import (
    get_data_from_website,
    process_website_data,    
)


class IncorrectEmailError(Exception):
    """Raises if email is incorrect."""


class EnrichAPI(models.AbstractModel):
    _name = 'enrich.api'
    _description = 'Lead Enrichment API'

    @api.model
    def _request_enrich(self, lead_email: EmailStr):
        at_index = lead_email.find('@')
        if at_index == -1:
            raise IncorrectEmailError()        
        domain = lead_email[at_index + 1:]
        home_url = 'https://' + domain.com
        url_prefix = home_url
        website_data = get_data_from_website(url_prefix, home_url)
        return process_website_data(website_data)
