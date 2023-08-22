import requests
from http import HTTPStatus
from bs4 import (
    BeautifulSoup,
    Tag,
)
from typing import (
    Optional,
)
from pydantic import (
    HttpUrl,
    AnyUrl, 
)
from .keywords import CONTACT_STRINGS


PARSER = 'html.parser'


class SiteURLSearcher:
    """Search for 'Contacts' page URL."""
    def __init__(self, url_prefix: HttpUrl, home_url: HttpUrl) -> None:
        self._url_prefix = url_prefix
        self._home_url = home_url
        response = requests.get(self._home_url)
        if response.status_code == HTTPStatus.OK:
            self._home_soup = BeautifulSoup(response.text, PARSER)
        else:
            raise ValueError(f"Invalid URL: {self._home_url}. Status code: {response.status_code}")
        self._contact_url: Optional[str] = None

    def is_link_to_contacts(self, link: Tag) -> bool:
        href: AnyUrl = link.get('href')
        text: str = link.get_text().lower()
        for contact_string in CONTACT_STRINGS:
            if contact_string in href or contact_string in text:
                return True
        return False

    def _href_padding(self, href: AnyUrl) -> HttpUrl:
        if not href.startswith(self._url_prefix):
            href = self._url_prefix + href
        return href

    def find_contact_url(self) -> Optional[str]:
        for link in self._home_soup.find_all('a', href=True):
            href: str = link.get('href')
            if self.is_link_to_contacts(link):
                self._contact_url = href
                return self._href_padding(href)
        return self._contact_url
