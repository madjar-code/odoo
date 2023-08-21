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
    is_common = fields.Boolean(
        string='Is the property common?', default=True)
    value = fields.Char('Property Value', required=False)

    lead_id = fields.Many2one('crm.lead',
                              required=False,
                              string='Related Lead',
                              ondelete='cascade')

    def unlink(self):
        self.many2one_field.unlink()
        return super(CRMProperty, self).unlink()


class CRMPropertyDescription(models.Model):
    _name = 'crm.prop.description'
    _description = 'Lead Property Description'

    name = fields.Char('Property Name', required=True)
    prop_type = fields.Selection(
        selection=[(item.value, item.name) for item in PropertyType],
        string='Property Type',
    )


class CRMPropertyValue(models.Model):
    _name = 'crm.prop.value'
    _description = 'Lead Property Value'

    value = fields.Char('Property Value', required=False)
    prop_description_id = fields.Many2one(
        'crm.prop.description', 'Property Description', required=True)
    lead_id = fields.Many2one(
        'crm.lead', string='Related Lead', required=True)
