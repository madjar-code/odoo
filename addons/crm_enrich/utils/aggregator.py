from typing import (
    Set,
    Dict,
    Optional,
    NamedTuple,
    TypeAlias,
    DefaultDict,
)
from pydantic import (
    EmailStr,
    HttpUrl,
)
from pycountry_convert import\
    country_name_to_country_alpha2
from geopy.geocoders import (
    Nominatim,
    Bing,
)
from .parsers import (
    SiteURLSearcher,
    WebsitePageParser,
    LinkedInEnrichParser,
)
from .enrich_private import BING_API_KEY


PhoneNumber: TypeAlias = str
AddressType: TypeAlias = str


class WebsitePageData(NamedTuple):
    email_addresses: Set[EmailStr]
    phone_numbers: Set[PhoneNumber]
    social_links: Set[HttpUrl]
    site_names: DefaultDict[str, int]


def get_data_from_website(url_prefix: HttpUrl, home_url: HttpUrl)\
        -> Dict[str, Optional[WebsitePageData]]:
    contact_url = None
    try:
        site_url_searcher = SiteURLSearcher(url_prefix, home_url)
        contact_url = site_url_searcher.find_contact_url()
        home_page_parser = WebsitePageParser(home_url)
        home_page_data = WebsitePageData(
            email_addresses=home_page_parser.get_email_addresses(),
            phone_numbers=home_page_parser.get_phone_numbers(),
            social_links=home_page_parser.get_social_links(),
            site_names=home_page_parser.get_site_names()
        )
    except Exception as e:
        print('Problem with home page URL')

    contact_page_data = None
    if contact_url:
        try:
            contact_page_parser = WebsitePageParser(contact_url)
            contact_page_data = WebsitePageData(
                email_addresses=contact_page_parser.get_email_addresses(),
                phone_numbers=contact_page_parser.get_phone_numbers(),
                social_links=contact_page_parser.get_social_links(),
                site_names=contact_page_parser.get_site_names()
            )
        except Exception as e:
            print('Problem with contact page URL')

    return {
        'home_page': home_page_data,
        'contact_page': contact_page_data
    }


def get_data_from_linkedin(linkedin_url: HttpUrl) -> Dict[str, str]:
    try:
        linkedin_parser = LinkedInEnrichParser(linkedin_url)
        linkedin_data = linkedin_parser.get_overview_data()
        linkedin_data['Address'] = linkedin_parser.get_location()
        linkedin_data['Name'] = linkedin_parser.get_title()
        linkedin_data['Phone'] = linkedin_parser.get_phone()
        return linkedin_data
    except:
        return None
    finally:
        linkedin_parser._quit()


class AddressData(NamedTuple):
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]
    country_code: Optional[str]


def process_address_string_by_bing(
        initial_address: AddressType) -> Optional[AddressData]:
    geolocator = Bing(api_key=BING_API_KEY)
    initial_location = geolocator.geocode(initial_address)

    if not initial_location:
        return

    latitude, longitude = initial_location.latitude, initial_location.longitude

    location = geolocator.reverse(f'{latitude},{longitude}')
    address = location.raw['address']
    country = address.get('countryRegion')
    country_code = country_name_to_country_alpha2(country)
    locality = address.get('locality')
    street = address.get('addressLine')
    zip_code = address.get('postalCode')

    return AddressData(
        country=country,
        country_code=country_code,
        state=None,
        city=locality,
        zip_code=zip_code,
        street=street,
    )._asdict()


def process_address_string_by_nominatim(
        initial_address: AddressType) -> Optional[AddressData]:
    geolocator = Nominatim(user_agent='my-custom-application')
    initial_location = geolocator.geocode(initial_address)

    if not initial_location:
        return

    latitude, longitude = initial_location.latitude, initial_location.longitude

    location = geolocator.reverse(f'{latitude},{longitude}', language='en')
    address = location.raw['address']
    country = address.get('country')
    country_code = address.get('country_code')
    street = address.get('house_number') +\
             ' ' + address.get('road')
    state = address.get('state')
    city = address.get('city')    
    zip_code = address.get('postcode')
    return AddressData(
        country=country,
        country_code=country_code,
        state=None,
        city=city,
        zip_code=zip_code,
        street=street,
    )._asdict()


def get_linkedin_url_by_website_data(
        website_page_data: WebsitePageData) -> Optional[HttpUrl]:
    for social_link in website_page_data.social_links:
        if 'linkedin' in social_link:
            return social_link


def get_facebook_url_by_website_data(
        website_page_data: WebsitePageData) -> Optional[HttpUrl]:
    for social_link in website_page_data.social_links:
        if 'facebook' in social_link:
            return social_link


class TargetDataUnit(NamedTuple):
    email: Optional[EmailStr]
    phone: Optional[PhoneNumber]
    social_links: Optional[Set[HttpUrl]]
    partner_name: Optional[str]
    address: Optional[AddressData]
    website: Optional[HttpUrl]


def aggregate_data(url_prefix: HttpUrl, home_url: HttpUrl) -> TargetDataUnit:
    website_data = get_data_from_website(url_prefix, home_url)
    home_page_data = website_data['home_page']
    contact_page_data = website_data['contact_page']

    email = None
    phone = None
    partner_name = None
    social_links = None
    address = None
    website = home_url

    if home_page_data:
        if home_page_data.email_addresses:
            email = home_page_data.email_addresses.pop()
        if home_page_data.phone_numbers:
            phone = home_page_data.phone_numbers.pop()
        if home_page_data.social_links:
            social_links = home_page_data.social_links

    if contact_page_data:
        if contact_page_data.email_addresses:
            email = contact_page_data.email_addresses.pop()
        if contact_page_data.phone_numbers:
            phone = contact_page_data.phone_numbers.pop()
        if contact_page_data.social_links:
            social_links = contact_page_data.social_links
        if contact_page_data.site_names:
            site_names: DefaultDict = contact_page_data.site_names
            max_name = max(site_names, key=site_names.get)
            partner_name = max_name

    linkedin_url_1: Optional[HttpUrl] =\
        get_linkedin_url_by_website_data(home_page_data)
    linkedin_url = None
    if linkedin_url_1:
        if linkedin_url_1.endswith('/'):
            linkedin_url = linkedin_url_1 + 'about/'
        else:
            linkedin_url = linkedin_url_1 + '/about/'

    try:
        facebook_url: Optional[HttpUrl] =\
            get_facebook_url_by_website_data(home_page_data)
        if 'profile.php?id=' in facebook_url:
            facebook_url += '&sk=about'
        else:
            facebook_url += 'about/' if facebook_url.endswith('/') else '/about/'
    except Exception:
        facebook_url = None

    address_data = None
    linkedin_data = None
    facebook_data = None
    if linkedin_url:
        try:
            linkedin_data = get_data_from_linkedin(linkedin_url)
            address = linkedin_data.get('Address')
            if linkedin_data.get('Name'):
                partner_name = linkedin_data['Name']
            if linkedin_data.get('Phone'):
                phone = linkedin_data['Phone']
            if address:
                address_data = process_address_string_by_bing(address)
        except Exception:
            address_data = None

    return TargetDataUnit(
        email=email, 
        phone=phone,
        partner_name=partner_name,
        social_links=social_links,
        address=address_data,
        website=website
    )._asdict()
