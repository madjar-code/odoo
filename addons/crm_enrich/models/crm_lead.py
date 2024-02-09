import logging
from datetime import datetime
from enum import Enum
from typing import (
    Dict,
    Any,
)
from pydantic import EmailStr
from psycopg2 import OperationalError
from odoo import _, api, fields, models, tools
from ..utils.aggregator import aggregate_data


_logger = logging.getLogger(__name__)


class IncorrectEmailError(Exception):
    """Raises if email is incorrect."""


class EnrichStatus(str, Enum):
    not_enriched = 'Not Enriched'
    enriching = 'Enriching'
    enriched = 'Enriched'
    failed = 'Failed'


class Lead(models.Model):
    _inherit = 'crm.lead'

    # enrich_done = fields.Boolean(string='Enrichment done')
    enrich_status = fields.Selection(
        selection=[(item.value, item.name)
                   for item in EnrichStatus],
        string='Lead Enrich State',
        default=EnrichStatus.not_enriched,
        store=True,
    )
    show_enrich_button = fields.Boolean(
        string='Allow manual enrich',
        compute='_compute_show_enrich_button'
    )

    @api.depends(
        'email_from',
        'probability',
        'enrich_status',
    )
    def _compute_show_enrich_button(self):
        for lead in self:
            if not lead.active or not lead.email_from\
                    or lead.email_state == 'incorrect'\
                    or lead.enrich_status == EnrichStatus.enriched\
                    or lead.probability == 100:
                lead.show_enrich_button = False
            else:
                lead.show_enrich_button = True

    def enrich(self):
        batches = [self[index:index + 50] for index in range(0, len(self), 50)]
        for leads in batches:
            with self._cr.savepoint():
                try:
                    self._cr.execute(
                            "SELECT 1 FROM {} WHERE id in %(lead_ids)s FOR UPDATE NOWAIT".format(self._table),
                            {'lead_ids': tuple(leads.ids)}, log_exceptions=False)
                    for lead in leads:
                        if lead.probability == 100 or not lead.email_from or\
                            lead.enrich_status == EnrichStatus.enriched:
                            continue
                        lead.write({'enrich_status': EnrichStatus.enriching})
                        normalized_email = tools.email_normalize(lead.email_from)
                        if not normalized_email:
                            lead.write({'enrich_status': EnrichStatus.failed})
                            lead.message_post_with_view(
                                'crm_enrich.mail_message_lead_enrich_no_email',
                                subtype_id=self.env.ref('mail.mt_note').id
                            )
                        lead = self.env['crm.lead'].search([
                            ('id', '=', lead.id)
                        ])
                        self._create_task_for_enrich(lead.id, normalized_email)
                        # self._enrich_lead_by_id(
                        #     lead_id=lead.id,
                        #     email=normalized_email
                        # )
                except OperationalError:
                    _logger.error('A batch of leads could not be enriched :%s', repr(leads))
                    continue
            if not self.env.registry.in_test_mode():
                self.env.cr.commit()

    def _create_task_for_enrich(self, lead_id: int, email: EmailStr) -> None:
        model_id = self.env['ir.model'].\
            search([('model', '=', 'crm.lead')]).id

        args = f"{lead_id}, '{email}'"

        self.env['ir.cron'].create({
            'name': f'Enrich Lead {lead_id} Task',
            'model_id': model_id,
            'state': 'code',
            'code': f'model._enrich_lead_by_id({args})',
            'interval_number': 1,
            'interval_type': 'minutes',
            'nextcall': datetime.now(),
            'numbercall': 1,
            'doall': False,
            'active': True,
        })

    def _enrich_lead_by_id(self, lead_id: int, email: EmailStr) -> None:
        lead = self.env['crm.lead'].search([
            ('id', '=', lead_id)
        ])
        try:
            enrich_response = self._request_enrich({lead.id: email})
        except Exception as e:
            _logger.info('Sent lead item %s enrich requests: failed with exception %s', len(lead), e)
            lead.write({'enrich_status': EnrichStatus.failed})
        else:
            _logger.info('Sent lead item %s enrich requests: success', len(lead))
            self._enrich_from_response(enrich_response)
            lead.write({'enrich_status': EnrichStatus.enriched})

    @api.model
    def _enrich_from_response(self, enrich_response):
        """
        Handle from the service and enrich the lead accordingly
        :param enrich_response: dict {lead_id: company data}
        """

        for lead in self.search([('id', 'in', list(enrich_response.keys()))]):
            extracted_data = enrich_response.get(lead.id)
            if not extracted_data:
                lead.write({'enrich_status': EnrichStatus.enriched})
                continue

            values: Dict[str, Any] = dict()

            self._update_contact_fields(lead, extracted_data, values)

            if extracted_data.get('address'):
                self._update_address_fields(lead, extracted_data, values)        

            if extracted_data.get('social_links'):
                self._add_social_links(lead, extracted_data, values)
            lead.write(values)

    def _update_contact_fields(
                self,
                lead: 'Lead',
                extracted_data: Dict[str, Any],
                values: Dict[str, Any]
            ) -> None:
        initial_email = lead.email_from
        extracted_email = extracted_data.get('email')
        if extracted_email and initial_email and\
                extracted_email != initial_email:
            values['email_cc'] = extracted_email

        initial_phone = lead.phone
        extracted_phone = extracted_data.get('phone')
        if extracted_phone and initial_phone and\
                extracted_phone != initial_phone:
            values['mobile'] = extracted_phone

        if not lead.website:
            values['website'] = extracted_data.get('website')
        if not lead.phone:
            values['phone'] = extracted_data.get('phone')
        if not lead.partner_name:
            values['partner_name'] = extracted_data.get('partner_name')

    def _update_address_fields(
                self,
                lead: 'Lead',
                extracted_data: Dict[str, Any],
                values: Dict[str, Any]
            ) -> None:
        address_data = extracted_data['address']
        if not lead.street:
            values['street'] = address_data.get('street')
        if not lead.zip:
            values['zip'] = address_data.get('zip_code')
        if not lead.city:
            values['city'] = address_data.get('city')
        if not lead.country_id:
            country_code = address_data.get('country_code')
            if country_code:
                country = self.env['res.country'].\
                    search([('code', '=', country_code.upper())], limit=1)
            if country:
                values['country_id'] = country.id

    def _add_social_links(
                self,
                lead: 'Lead',
                extracted_data: Dict[str, Any],
                values: Dict[str, Any]
            ) -> None:
        crm_property_value_table = self.env['crm.prop.value']
        crm_property_description_table = self.env['crm.prop.description']

        prop_description = crm_property_description_table.sudo().search(
                [('name', '=', 'social_link')], limit=1)
        if not prop_description:
            prop_description = crm_property_description_table.sudo().create({
                'name': 'social_link',
                'prop_type': 'char',
            })
        for social_link in extracted_data['social_links']:
            if crm_property_value_table.sudo().search(
                    [('value', '=', social_link),
                     ('lead_id', '=', lead.id)], limit=1):
                continue
            crm_property_value_table.sudo().create({
                'value': social_link,
                'prop_description_id': prop_description[0].id,
                'lead_id': lead.id
            })

    def _request_enrich(self, lead_emails: Dict[int, EmailStr]) -> Dict:
        result_data = dict()
        for lead_id, lead_email in lead_emails.items():
            at_index = lead_email.find('@')
            if at_index == -1:
                raise IncorrectEmailError()
            domain = lead_email[at_index + 1:]
            home_url = 'https://' + domain
            url_prefix = home_url
            result_data[lead_id] = aggregate_data(url_prefix, home_url)
        return result_data

    def _merge_get_fields_specific(self):
        return {
            ** super(Lead, self)._merge_get_fields_specific(),
            'enrich_status': lambda fname, leads: any(lead.enrich_status for lead in leads),
        }
