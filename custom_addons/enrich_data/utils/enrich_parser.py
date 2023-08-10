import re
import requests
from bs4 import (
    BeautifulSoup,
    Tag,
)
from typing import (
    Set,
    List,
    TypeAlias,
)
from pydantic import (
    HttpUrl,
    EmailStr,
)
from http import HTTPStatus
from keywords import (
    SOCIAL_NETWORKS,
    ADDRESS_KEYWORDS
)


PARSER = 'html.parser'

PhoneNumber: TypeAlias = str
AddressType: TypeAlias = str


class EnrichParser:
    def __init__(self, url: HttpUrl) -> None:
        self._url = url
        response = requests.get(self._url)
        if response.status_code == HTTPStatus.OK:
            self._soup = BeautifulSoup(response.text, PARSER)
        else:
            raise ValueError(f"Invalid URL: {self._url}. Status code: {response.status_code}")
        self._social_regex = r'(' + '|'.join(SOCIAL_NETWORKS) + r')'

    def get_social_links(self) -> Set[HttpUrl]:
        social_links = set()
        for link in self._soup.find_all('a', href=True):
            href: str = link.get('href')
            if re.search(self._social_regex, href):
                social_links.add(href)
        return social_links

    def get_phone_numbers(self) -> Set[PhoneNumber]:
        phone_numbers = set()
        for link in self._soup.find_all('a', href=True):
            href: str = link.get('href')
            if href.startswith('tel:'):
                phone_number = re.sub(r'\D', '', link.get_text())
                phone_numbers.add(phone_number)
        return phone_numbers

    def get_email_addresses(self) -> Set[EmailStr]:
        email_addresses = set()
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        page_text = self._soup.get_text()
        email_addresses.update(email_pattern.findall(page_text))
        return email_addresses

    def get_addresses(self) -> Set[AddressType]:
        # TODO: Create more flexible and good validation
        addresses = set()
        element: Tag = self._soup.find(attrs={'title': 'address'})
        if element:
            raw_address = element.get_text()
            cleaned_address = raw_address.strip('\n ')
            addresses.add(cleaned_address)
        all_texts: List[str] = []
        for content in self._soup.stripped_strings:
            all_texts.append(content)
        for text in all_texts:
            if any(char.isdigit() for char in text):
                for key in ADDRESS_KEYWORDS:
                    pattern = re.compile(rf'{re.escape(key)}', re.IGNORECASE)
                    if len(text) < 64 and re.search(pattern, text):
                        addresses.add(text)
        return addresses
