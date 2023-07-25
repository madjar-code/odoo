from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'res.users'

    def _compute_checklist_count(self):
        for c in self:
            c.userchecklist_count = (
                self.env['crm.lead.checklist']
                    .search_count([('id', '>', 0)])
            )

    userchecklist_ids = fields.Many2many(
        'crm.lead.checklist', 'res_user_checklist_rel',
        'id', 'checklist_id', string='User checklist')

    userchecklist_count = fields.Integer(compute='_compute_checklist_count')
