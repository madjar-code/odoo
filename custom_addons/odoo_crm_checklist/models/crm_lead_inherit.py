from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.depends('checkbox_ids')
    def _compute_checkbox_count(self):
        for lead in self:
            lead.checkbox_count = len(lead.checkbox_ids)

    def _compute_checklist_total(self):
        for c in self:
            c.total_checklist = (
                self.env['crm.lead.checklist'].search_count([])
            )

    @api.depends('checkbox_ids', 'total_checklist')
    def _compute_progress(self):
        for lead in self:
            if lead.checkbox_count > 0.0:
                if lead.checkbox_count >= lead.total_checklist:
                    lead.progress = 100
                else:
                    lead.progress = round(100.0 * lead.checkbox_count / lead.total_checklist, 2)
            else:
                lead.progress = 0.0

    checkbox_ids = fields.Many2many(
        'crm.lead.checklist', 'checkbox_checklist_rel',
        'id', 'checklist_id', string='Checkboxes')

    checkbox_count = fields.Integer(compute='_compute_checkbox_count', store=True)
    total_checklist = fields.Integer(compute='_compute_checklist_total')

    progress = fields.Float('Progress', compute='_compute_progress', store=True,
                            group_operator='avg', help='Display progress of current lead.')
