from enum import Enum
from odoo import (
    api,
    models,
    fields,
)


class KnowledgeState(str, Enum):
    draft = 'draft'
    published = 'published'
    deactivated = 'deactivated'


class Category(models.Model):
    _name = 'knowledges.category'
    _description = 'Category'

    _rec_name = 'title'

    title = fields.Char(
        string='Category Title',
        required=True,
    )


class KnowledgeItem(models.Model):
    _name = 'knowledges.item'
    _description = 'Knowledge Item'

    _rec_names_search = 'title'
    _rec_name = 'title'

    icon = fields.Image(
        string='Icon',
        attachment=True
    )
    title = fields.Char(
        string='Title',
        required=True
    )
    body = fields.Html(
        string='Body',
        required=True,
        widget='html'
    )
    author_id = fields.Many2one(
        'res.users',
        string='Author',
        default=lambda self: self.env.user
    )
    parent_id = fields.Many2one(
        'knowledges.item',
        string='Parent Article',
    )
    category_id = fields.Many2one(
        'knowledges.category',
        string='Knowledge Category',
    )
    state = fields.Selection(
        selection=[(item.value, item.name)
                   for item in KnowledgeState],
        string='State',
        default=KnowledgeState.draft,
    )

    editor_ids = fields.Many2many(
        'res.users',
        string='Editors',
    )

    shareable_link = fields.Char(
        string='Shareable Link',
        compute='_compute_shareable_link',
        store=True,
        readonly=True,
    )

    @api.depends()
    def _compute_shareable_link(self):
        for item in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            item.shareable_link = f'{base_url}/web#id={item.id}&cids=1&model=knowledges.item'

    def action_generate_link(self):
        for item in self:
            item._compute_shareable_link()

    def action_publish(self):
        print(f'\n"{self.title}" was published!\n')
        self.write({'state': KnowledgeState.published})
        # return self.set_main_tree_view()

    def action_move_to_trash(self):
        print(f'\n"{self.title}" was moved to trash!\n')
        self.write({'state': KnowledgeState.deactivated})
        # return self.set_main_tree_view()

    def action_save(self):
        print(f'\n"{self.title}" was saved!\n')
        # return self.set_main_tree_view()

    def set_main_tree_view(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Knowledges',
            'res_model': 'knowledges.item',
            'view_mode': 'tree',
            'view_id': False,
            'views': [(False, 'tree'), (False, 'form')],
            'target': 'main',
            'res_id': self.id,
            'context': self.env.context,
        }

    # @api.model
    # def create(self, vals):
    #     record = super(KnowledgeItem, self).create(vals)
    #     author = record.author_id

    #     group_admin = self.env['res.groups'].search([('name', '=', 'Knowledges Admin')], limit=1)
    #     if author not in group_admin.users:
    #         group_editor = self.env['res.groups'].search([('name', '=', 'Knowledges Editor')], limit=1)
    #         group_viewer = self.env['res.groups'].search([('name', '=', 'Knowledges Viewer')], limit=1)

    #         group_editor_id = group_editor.id if group_editor else False
    #         group_viewer_id = group_viewer.id if group_viewer else False

    #         group_ids = [
    #             (4, group_editor_id),
    #             (4, group_viewer_id)
    #         ]
    #         author.write({'groups_id': group_ids})

    #     return record
