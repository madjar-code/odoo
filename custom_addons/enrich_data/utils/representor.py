from typing import (
    Set,
    Dict,
    Optional,
    NamedTuple,
    TypeAlias,
    DefaultDict,
)
from enum import Enum
from pydantic import (
    EmailStr,
    HttpUrl,
)
import geopy.geocoders
from geopy.location import Location
from geopy.geocoders import Nominatim

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
    site_names: DefaultDict[str, int]


class AddressData(NamedTuple):
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]


class TargetDataUnit(NamedTuple):
    email: Optional[EmailStr]
    phone: Optional[PhoneNumber]
    social_link: Optional[HttpUrl]
    address: Optional[AddressData]
    site_name: Optional[str]


class WebsiteDataExtractor:
    def __init__(self, url: HttpUrl) -> None:
        self.parser = EnrichParser(url)

    def get_data(self):
        return ParsedData(
            email_addresses=self.parser.get_email_addresses(),
            phone_numbers=self.parser.get_phone_numbers(),
            social_links=self.parser.get_social_links(),
            addresses=self.parser.get_addresses(),
            site_names=self.parser.get_site_names()
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


def process_address_string(initial_address: AddressType) -> Optional[AddressData]:
    geopy.geocoders.options.default_user_agent = 'my_app'
    geolocator = Nominatim()
    initial_location: Location = geolocator.geocode(initial_address)
    
    if not initial_location:
        return None

    latitude, longitude = initial_location.latitude, initial_location.longitude

    location = geolocator.reverse(f'{latitude},{longitude}', language='en')
    address = location.raw['address']
    country = address.get('country')
    road = address.get('road')
    state = address.get('state')
    city = address.get('city')    
    zip_code = address.get('postcode')

    return AddressData(
        country=country, 
        state=state,
        city=city,
        zip_code=zip_code,
        street=road
    )._asdict()


def process_website_data(website_data:\
        Dict[WebsitePage, Optional[ParsedData]]) -> TargetDataUnit:
    contact_page_data = website_data[WebsitePage.CONTACT_PAGE.value]
    home_page_data = website_data[WebsitePage.HOME_PAGE.value]

    email = None
    phone = None
    social_link = None
    address = None
    site_name = None

    if contact_page_data:
        if contact_page_data.email_addresses:
            email = contact_page_data.email_addresses.pop()
        if contact_page_data.phone_numbers:
            phone = contact_page_data.phone_numbers.pop()
        if contact_page_data.social_links:
            social_link = contact_page_data.social_links.pop()
        if contact_page_data.addresses:
            address = contact_page_data.addresses.pop()
            address_data = process_address_string(initial_address=address)
        if contact_page_data.site_names:
            site_names: DefaultDict = contact_page_data.site_names
            max_name = max(site_names, key=site_names.get)
            site_name = max_name

    if home_page_data.email_addresses and not email:
        email = home_page_data.email_addresses.pop()
    if home_page_data.phone_numbers and not phone:
        phone = home_page_data.phone_numbers.pop()
    if home_page_data.social_links and not social_link:
        social_link = home_page_data.social_links.pop()
    if home_page_data.addresses and not address:
        address = home_page_data.addresses.pop()
    if home_page_data.site_names and not site_name:
        site_names: DefaultDict = home_page_data.site_names
        max_name = max(site_names, key=site_names.get)
        site_name = max_name

    return TargetDataUnit(email, phone, social_link, address_data, site_name)._asdict()
