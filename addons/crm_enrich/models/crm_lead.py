import logging
from typing import Dict
from pydantic import EmailStr
from psycopg2 import OperationalError
from odoo import _, api, fields, models, tools
from ..utils.aggregator import aggregate_data


_logger = logging.getLogger(__name__)


class IncorrectEmailError(Exception):
    """Raises if email is incorrect."""


class Lead(models.Model):
    _inherit = 'crm.lead'

    enrich_done = fields.Boolean(string='Enrichment done')
    show_enrich_button = fields.Boolean(string='Allow manual enrich', compute='_compute_show_enrich_button')

    @api.depends('email_from',
                 'probability',
                 'enrich_done',)
    def _compute_show_enrich_button(self):
        for lead in self:
            if not lead.active or not lead.email_from\
                    or lead.email_state == 'incorrect'\
                    or lead.enrich_done\
                    or lead.probability == 100:
                lead.show_enrich_button = False
            else:
                lead.show_enrich_button = True

    def enrich(self, from_cron=False):
        batches = [self[index:index + 50] for index in range(0, len(self), 50)]
        for leads in batches:
            lead_emails = dict()
            with self._cr.savepoint():
                try:
                    self._cr.execute(
                            "SELECT 1 FROM {} WHERE id in %(lead_ids)s FOR UPDATE NOWAIT".format(self._table),
                            {'lead_ids': tuple(leads.ids)}, log_exceptions=False)
                    for lead in leads:
                        if lead.probability == 100 or lead.enrich_done:
                            continue
                        if not lead.email_from:
                            continue

                        normalized_email = tools.email_normalize(lead.email_from)
                        if not normalized_email:
                            lead.message_post_with_view(
                                'crm_enrich.mail_message_lead_enrich_no_email',
                                subtype_id=self.env.ref('mail.mt_note').id
                            )
                        # TODO: Add mail blacklist analyzer.
                        lead_emails[lead.id] = normalized_email
                    if lead_emails:
                        try:
                            # print(f'\n\n{lead_emails}\n\n')
                            enrich_response = self._request_enrich(lead_emails)
                        except Exception as e:
                            _logger.info('Sent batch %s enrich requests: failed with exception %s', len(lead_emails), e)
                        else:
                            _logger.info('Sent batch %s enrich requests: success', len(lead_emails))
                            self._enrich_from_response(enrich_response)
                except OperationalError:
                    _logger.error('A batch of leads could not be enriched :%s', repr(leads))
                    continue
            if not self.env.registry.in_test_mode():
                self.env.cr.commit()

    @api.model
    def _enrich_from_response(self, enrich_response):
        """
        Handle from the service and enrich the lead accordingly
        :param enrich_response: dict {lead_id: company data}
        """
        for lead in self.search([('id', 'in', list(enrich_response.keys()))]):
            extracted_data = enrich_response.get(lead.id)
            if not extracted_data:
                lead.write({'enrich_done': True})
                continue
            values = {'enrich_done': True}
            values = {}

            if not lead.website and extracted_data.get('website'):
                values['website'] = extracted_data['website']
            if not lead.phone and extracted_data.get('phone'):
                values['phone'] = extracted_data['phone']
            if not lead.partner_name and extracted_data.get('partner_name'):
                values['partner_name'] = extracted_data['partner_name']
            if not lead.street and extracted_data.get('address'):
                values['street'] = extracted_data['address'].get('street')
            if not lead.zip and extracted_data.get('address'):
                values['zip'] = extracted_data['address'].get('zip_code')
            if not lead.city and extracted_data.get('address'):
                values['city'] = extracted_data['address'].get('city')
            if not lead.country_id and extracted_data.get('address'):
                country_code: str = extracted_data['address'].get('country_code')
                country = self.env['res.country'].\
                    search([('code', '=', country_code.upper())], limit=1)
                if country:
                    values['country_id'] = country.id
            lead.write(values)

    def _request_enrich(self, lead_emails: Dict[int, EmailStr]) -> Dict:
        result_data = dict()
        for lead_id, lead_email in lead_emails.items():
            at_index = lead_email.find('@')
            if at_index == -1:
                raise IncorrectEmailError()
            domain = lead_email[at_index + 1:]
            home_url = 'https://' + domain
            # print(f'\n\n{home_url}\n\n')
            url_prefix = home_url
            result_data[lead_id] = aggregate_data(url_prefix, home_url)
        return result_data

    def _merge_get_fields_specific(self):
        return {
            ** super(Lead, self)._merge_get_fields_specific(),
            'enrich_done': lambda fname, leads: any(lead.enrich_done for lead in leads),
        }
