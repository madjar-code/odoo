from odoo import fields, models
from ..routers import router

class FastapiEndpoint(models.Model):

    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("crm", "CRM Endpoint")], ondelete={"crm": "cascade"}
    )

    def _get_fastapi_routers(self):
        if self.app == "crm":
            return [router]
        return super()._get_fastapi_routers()