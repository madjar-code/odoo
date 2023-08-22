import re
import requests
from urllib.parse import urlparse
from bs4 import (
    BeautifulSoup,
    Tag,
)
from typing import (
    Set,
    List,
    Dict,
    
    TypeAlias,
)
from pydantic import (
    HttpUrl,
    EmailStr,
)
from collections import defaultdict
from http import HTTPStatus
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from .keywords import (
    SOCIAL_NETWORKS,
    ADDRESS_KEYWORDS
)


PARSER = 'html.parser'

PhoneNumber: TypeAlias = str
AddressType: TypeAlias = str


class EnrichParser:
    def __init__(self, url: HttpUrl, site_name: str = None) -> None:
        self._url = url
        self._site_name = site_name
        if not site_name:
            parsed_url = urlparse(url)
            parts = parsed_url.netloc.split('.')
            self._site_name = parts[0] if parts[0] != 'www' else parts[1]
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
                    if len(text) > 8 and len(text) < 80 and re.search(pattern, text):
                        addresses.add(text)
        return addresses

    def get_site_names(self) -> defaultdict[str, int]:
        """
        This method is used to extract all names
        that are similar to the company name
        """
        names_dict = defaultdict(int)
        name_pattern = r'\s*'.join(self._site_name)
        text: str = self._soup.get_text()
        name_matches = re.findall(name_pattern, text, flags=re.IGNORECASE)
        for match in name_matches:
            names_dict[match] += 1
        return names_dict


class LinkedInEnrichParser:
    def __init__(self, linkedin_url: HttpUrl) -> None:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service,
                                       options=chrome_options)
        self.linkedin_url = linkedin_url
        self._linkedin_login()
        self.driver.get(linkedin_url)
        src = self.driver.page_source
        self.soup = BeautifulSoup(src, 'lxml')

    def _linkedin_login(self) -> None:
        self.driver.get('https://linkedin.com/uas/login')
        username = self.driver.find_element(By.ID, 'username')
        username.send_keys('evan.madjar@datadrivemd.com')
        password = self.driver.find_element(By.ID, 'password')
        password.send_keys('!KZT9T:sr(8s^4k')
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

    def get_overview_data(self) -> Dict[str, str]:
        about = self.soup.find('dl', {'class': 'overflow-hidden'})
        dt_elements = about.find_all('dt')
        dd_elements = about.find_all('dd')
        data = dict()
        for dt, dd in zip(dt_elements, dd_elements):
            dt_text = dt.get_text(strip=True)
            dd_text = dd.get_text(strip=True)
            data[dt_text] = dd_text
        return data

    def get_location(self) -> str:
        locations = self.soup.find('div', {'class': 'org-locations-module__card-spacing'})
        address_element = locations.find('p', class_='t-14 t-black--light t-normal break-words')
        if address_element:
            address_text = address_element.get_text(strip=True)
        return address_text