from typing import (
    Set,
    Dict,
    Optional,
    NamedTuple,
)
from .site_url_searcher import SiteNavigator
from .enrich_parser import EnrichParser


class ParsedData(NamedTuple):
    email_addresses: Set[str]
    phone_numbers: Set[str]
    social_links: Set[str]
    addresses: Set[str]


def get_data_from_website(url_prefix: str, home_url: str)\
        -> Dict[str, Optional[ParsedData]]:
    site_navigator = SiteNavigator(url_prefix, home_url)
    contact_url = site_navigator.find_contact_url()
    
    home_page_parser = EnrichParser(home_url)
    home_page_data = ParsedData(
        email_addresses=home_page_parser.get_email_addresses(),
        phone_numbers=home_page_parser.get_phone_numbers(),
        social_links=home_page_parser.get_social_links(),
        addresses=home_page_parser.get_addresses()
    )._asdict()
    contact_page_data = None
    if contact_url:
        contact_page_parser = EnrichParser(contact_url)
        contact_page_data = ParsedData(
            email_addresses=contact_page_parser.get_email_addresses(),
            phone_numbers=contact_page_parser.get_phone_numbers(),
            social_links=contact_page_parser.get_social_links(),
            addresses=contact_page_parser.get_addresses()
        )._asdict()
    return {
        'home_page': home_page_data,
        'contact_page': contact_page_data
    }
