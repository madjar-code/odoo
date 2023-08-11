from typing import (
    Set,
    Dict,
    Optional,
    NamedTuple,
    TypeAlias,
)
from enum import Enum
from pydantic import (
    EmailStr,
    HttpUrl,
)
from .site_url_searcher import SiteURLSearcher
from .enrich_parser import EnrichParser


PhoneNumber: TypeAlias = str
AddressType: TypeAlias = str


class WebsitePage(Enum):
    HOME_PAGE = 'home_page'
    CONTACT_PAGE = 'contact_page'


class ParsedData(NamedTuple):
    email_addresses: Set[EmailStr]
    phone_numbers: Set[PhoneNumber]
    social_links: Set[HttpUrl]
    addresses: Set[AddressType]


class TargetDataUnit(NamedTuple):
    email: Optional[EmailStr]
    phone: Optional[PhoneNumber]
    social_link: Optional[HttpUrl]
    address: Optional[AddressType]


class WebsiteDataExtractor:
    def __init__(self, url: HttpUrl) -> None:
        self.parser = EnrichParser(url)

    def get_data(self):
        return ParsedData(
            email_addresses=self.parser.get_email_addresses(),
            phone_numbers=self.parser.get_phone_numbers(),
            social_links=self.parser.get_social_links(),
            addresses=self.parser.get_addresses()
        )


def get_data_from_website(url_prefix: HttpUrl, home_url: HttpUrl)\
        -> Dict[WebsitePage, Optional[ParsedData]]:
    site_url_searcher = SiteURLSearcher(url_prefix, home_url)
    contact_url = site_url_searcher.find_contact_url()
    
    home_page_extractor = WebsiteDataExtractor(home_url)
    home_page_data = home_page_extractor.get_data()

    contact_page_data = None
    if contact_url:
        contact_page_extractor = WebsiteDataExtractor(contact_url)
        contact_page_data = contact_page_extractor.get_data()
    return {
        WebsitePage.HOME_PAGE.value: home_page_data,
        WebsitePage.CONTACT_PAGE.value: contact_page_data
    }


def process_website_data(website_data:\
        Dict[WebsitePage, Optional[ParsedData]]) -> TargetDataUnit:
    contact_page_data = website_data[WebsitePage.CONTACT_PAGE.value]
    home_page_data = website_data[WebsitePage.HOME_PAGE.value]

    email = None
    phone = None
    social_link = None
    address = None

    if contact_page_data:
        if contact_page_data.email_addresses:
            email = contact_page_data.email_addresses.pop()
        if contact_page_data.phone_numbers:
            phone = contact_page_data.phone_numbers.pop()
        if contact_page_data.social_links:
            social_link = contact_page_data.social_links.pop()
        if contact_page_data.addresses:
            address = contact_page_data.addresses.pop()

    if home_page_data.email_addresses and not email:
        email = home_page_data.email_addresses.pop()
    if home_page_data.phone_numbers and not phone:
        phone = home_page_data.phone_numbers.pop()
    if home_page_data.social_links and not social_link:
        social_link = home_page_data.social_links.pop()
    if home_page_data.addresses and not address:
        address = home_page_data.addresses.pop()

    return TargetDataUnit(email, phone, social_link, address)._asdict()
