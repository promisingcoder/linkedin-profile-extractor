import requests
from bs4 import BeautifulSoup
import time
import logging
import random
import re

class SearxNGSearch:
    def __init__(self):
        self.search_engines = [
            'https://searx.be/search',
            'https://search.inetol.net/search',
            'https://priv.au/search',
            'https://northboot.xyz/search',
            'https://searx.rhscz.eu/search',
            'https://search.ononoki.org/search',
            'https://search.sapti.me/search',
            'https://www.gruble.de/search'
        ]
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'null',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"'
        }

    def clean_url(self, url):
        """Remove web.archive.org prefix from URLs."""
        if not url:
            return url
        
        # Pattern to match web.archive.org URLs
        pattern = r'https?://(?:www\.)?web\.archive\.org/web/\d*/(?:https?://)?(.+)'
        match = re.match(pattern, url)
        if match:
            cleaned_url = match.group(1)
            # Ensure the URL starts with https://
            if not cleaned_url.startswith('http'):
                cleaned_url = 'https://' + cleaned_url
            return cleaned_url
        return url

    def search_profiles(self, query):
        """Search for LinkedIn profiles using multiple search engines with fallback."""
        personal_profiles = set()
        company_profiles = set()
        
        data = {
            'q': query,
            'category_general': '1',
            'language': 'auto',
            'time_range': '',
            'safesearch': '0',
            'theme': 'simple'
        }

        for search_engine in self.search_engines:
            try:
                logging.info(f"Trying search engine: {search_engine}")
                response = requests.post(search_engine, headers=self.headers, data=data, timeout=30)
                
                if response.status_code == 200:
                    # Parse the response and extract LinkedIn URLs
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = soup.find_all('a', href=True)
                    
                    found_new_profiles = False
                    initial_personal_count = len(personal_profiles)
                    initial_company_count = len(company_profiles)
                    
                    for result in results:
                        url = result['href']
                        # Clean the URL before checking and storing
                        cleaned_url = self.clean_url(url)
                        
                        # Only process URLs that don't contain web.archive.org
                        if cleaned_url and 'web.archive.org' not in cleaned_url:
                            if 'linkedin.com/in/' in cleaned_url:
                                personal_profiles.add(cleaned_url)
                            elif 'linkedin.com/company/' in cleaned_url:
                                company_profiles.add(cleaned_url)
                    
                    # Check if we found any new profiles
                    new_personal = len(personal_profiles) - initial_personal_count
                    new_company = len(company_profiles) - initial_company_count
                    
                    if new_personal > 0 or new_company > 0:
                        found_new_profiles = True
                        logging.info(f"Found {new_personal} new personal profiles and {new_company} new company profiles from {search_engine}")
                    
                    # If we found profiles, we can stop trying other engines
                    if found_new_profiles:
                        break
                    else:
                        logging.info(f"No new profiles found from {search_engine}, trying next engine...")
                
                else:
                    logging.warning(f"Search request failed for {search_engine} with status code: {response.status_code}")
                    continue
                
            except requests.exceptions.RequestException as e:
                logging.warning(f"Error with search engine {search_engine}: {str(e)}")
                continue
            except Exception as e:
                logging.error(f"Unexpected error with search engine {search_engine}: {str(e)}")
                continue

        return personal_profiles, company_profiles 