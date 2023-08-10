from typing import (
    Set,
    Dict,
    Optional,
    NamedTuple,
)
from enum import Enum
from pydantic import HttpUrl
from .site_url_searcher import SiteNavigator
from .enrich_parser import EnrichParser


class WebsitePage(Enum):
    HOME_PAGE = 'home_page'
    CONTACT_PAGE = 'contact_page'


class ParsedData(NamedTuple):
    email_addresses: Set[str]
    phone_numbers: Set[str]
    social_links: Set[str]
    addresses: Set[str]


class WebsiteDataExtractor:
    def __init__(self, url: HttpUrl) -> None:
        self.parser = EnrichParser(url)

    def get_data(self):
        return ParsedData(
            email_addresses=self.parser.get_email_addresses(),
            phone_numbers=self.parser.get_phone_numbers(),
            social_links=self.parser.get_social_links(),
            addresses=self.parser.get_addresses()
        )._asdict()


def get_data_from_website(url_prefix: HttpUrl, home_url: HttpUrl)\
        -> Dict[WebsitePage, Optional[ParsedData]]:
    site_navigator = SiteNavigator(url_prefix, home_url)
    contact_url = site_navigator.find_contact_url()
    
    home_page_extractor = WebsiteDataExtractor(home_url)
    home_page_data = home_page_extractor.get_data()

    contact_page_data = None
    if contact_url:
        contact_page_extractor = WebsiteDataExtractor(contact_url)
        contact_page_data = contact_page_extractor.get_data()

    return {
        WebsitePage.HOME_PAGE: home_page_data,
        WebsitePage.CONTACT_PAGE: contact_page_data
    }
