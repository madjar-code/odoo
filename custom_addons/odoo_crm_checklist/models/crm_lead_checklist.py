from odoo import fields, models


class CrmLeadChecklist(models.Model):
    _name = 'crm.lead.checklist'
    _description = 'CRM Lead Checklist'
    _sql_constraints = [
        ('owner_name_uniq', 'unique (owner_id, name)', "Checklist name already exists!"),
    ]
    name = fields.Char('Checklist Name', required=True, translate=True)

    owner_id = fields.Many2one(
        'res.users', string='Owner', index=True,
        default=lambda self: self.env.user)
