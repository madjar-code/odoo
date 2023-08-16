from enum import Enum
from odoo import models, fields


class PropertyType(str, Enum):
    BOOLEAN = 'boolean'
    INTEGER = 'integer'
    FLOAT = 'float'
    CHAR = 'char'
    DATE = 'date'
    DATETIME = 'datetime'
    MANY2ONE = 'many2one'
    MANY2MANY = 'many2many'
    SELECTION = 'selection'
    TAGS = 'tags'


class CRMProperty(models.Model):
    _name = 'crm.property'
    _description = 'Properties for Leads'

    name = fields.Char('Property Title', required=True)
    type = fields.Selection(
        selection=[(item.value, item.name) for item in PropertyType],
        string='Property Type',
    )
    value = fields.Char('Property Value', required=True)

    lead_id = fields.Many2one('crm.lead',
                              required=False,
                              string='Related Lead',
                              ondelete='cascade')
