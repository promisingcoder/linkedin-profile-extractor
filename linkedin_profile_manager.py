import requests
from bs4 import BeautifulSoup
import time
import logging
import random
import json
import os
import openai
from browser import Browser, HeadlessBrowser
import re

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProfileType:
    PERSONAL = "personal"
    COMPANY = "company"

class LinkedInProfileManager:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.scraper = LinkedInProfileScraper()
        self.dork_generator = DorkGenerator(api_key=self.api_key)
        self.browser = None
        
        # Initialize separate sets for different profile types
        self.personal_profiles = set()
        self.company_profiles = set()
        
        self.profiles = []
        
    def initialize_browser(self):
        """Initialize the browser and load cookies"""
        try:
            self.browser = Browser()
            self.browser.load_cookies_from_file("cookies.txt")
            logging.info("Successfully initialized browser and loaded cookies")
            return True
        except Exception as e:
            logging.error(f"Error initializing browser: {e}")
            return False

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
        """Search for LinkedIn profiles using searx.ro."""
        headers = {
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

        data = {
            'q': query,
            'category_general': '1',
            'language': 'auto',
            'time_range': '',
            'safesearch': '0',
            'theme': 'simple'
        }

        try:
            response = requests.post('https://searx.ro/search', headers=headers, data=data)
            if response.status_code == 200:
                # Parse the response and extract LinkedIn URLs
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('a', href=True)
                
                for result in results:
                    url = result['href']
                    # Clean the URL before processing
                    cleaned_url = self.clean_url(url)
                    
                    if 'linkedin.com/in/' in cleaned_url:
                        self.personal_profiles.add(cleaned_url)
                    elif 'linkedin.com/company/' in cleaned_url:
                        self.company_profiles.add(cleaned_url)
                
                logging.info(f"Found {len(self.personal_profiles)} personal profiles and {len(self.company_profiles)} company profiles")
            else:
                logging.error(f"Search request failed with status code: {response.status_code}")
        
        except Exception as e:
            logging.error(f"Error during search: {str(e)}")

    def process_profiles(self, query, profile_type="both"):
        """Main method to process LinkedIn profiles"""
        # Generate search queries
        logging.info(f"Generating search queries for: {query}")
        dorks = self.dork_generator.generate_dorks(query, profile_type)
        
        if not dorks:
            logging.error("No search queries were generated")
            return False

        # Save generated dorks
        with open("generated_dorks.txt", 'w') as f:
            for dork in dorks:
                f.write(f"# {dork.get('explanation', 'No explanation provided')}\n")
                f.write(f"{dork.get('dork', '')}\n\n")

        # Search for profiles using each dork
        for dork in dorks:
            logging.info(f"Processing search query: {dork['dork']}")
            self.search_profiles(dork['dork'])
            # Add random delay between searches
            time.sleep(random.uniform(2, 5))

        # Save categorized profiles
        self.save_categorized_profiles()
        
        # Process profiles with appropriate instructions
        self.process_with_instructions()
        
        return True

    def save_categorized_profiles(self):
        """Save personal and company profiles to separate files"""
        if self.personal_profiles:
            with open("personal_profiles.txt", 'w') as f:
                for profile in self.personal_profiles:
                    f.write(f"{profile}\n")
            logging.info(f"Saved {len(self.personal_profiles)} personal profiles")

        if self.company_profiles:
            with open("company_profiles.txt", 'w') as f:
                for profile in self.company_profiles:
                    f.write(f"{profile}\n")
            logging.info(f"Saved {len(self.company_profiles)} company profiles")

    def process_with_instructions(self):
        """Process profiles with appropriate instructions"""
        try:
            # Initialize browser if not already initialized
            if not self.browser:
                if not self.initialize_browser():
                    return False

            # Process personal profiles
            if self.personal_profiles:
                # Create a batch file for processing
                with open("current_batch_profiles.txt", 'w') as f:
                    for profile in self.personal_profiles:
                        f.write(f"{profile}\n")
                
                # Execute personal profile instructions
                self.browser.execute_instructions("linkedin_profile_instructions.txt")
                
            # Process company profiles
            if self.company_profiles:
                # Create a batch file for processing
                with open("current_batch_profiles.txt", 'w') as f:
                    for profile in self.company_profiles:
                        f.write(f"{profile}\n")
                
                # Execute company profile instructions
                self.browser.execute_instructions("company_profile_instructions.txt")

            return True
            
        except Exception as e:
            logging.error(f"Error processing profiles: {e}")
            self._save_unprocessed_profiles()
            return False
        finally:
            if self.browser:
                self.browser.close()
                self.browser = None

    def _save_unprocessed_profiles(self):
        """Save any unprocessed profiles in case of errors"""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        if self.personal_profiles:
            filename = f"unprocessed_personal_profiles_{timestamp}.txt"
            with open(filename, 'w') as f:
                for profile in self.personal_profiles:
                    f.write(f"{profile}\n")
            logging.info(f"Saved unprocessed personal profiles to {filename}")
            
        if self.company_profiles:
            filename = f"unprocessed_company_profiles_{timestamp}.txt"
            with open(filename, 'w') as f:
                for profile in self.company_profiles:
                    f.write(f"{profile}\n")
            logging.info(f"Saved unprocessed company profiles to {filename}")

    def load_profiles(self, file_path):
        """Load profiles from a JSON file."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            profile = json.loads(line)
                            self.profiles.append(profile)
            return True
        except FileNotFoundError:
            logging.info(f"File not found: {file_path}, will create new file")
            return True
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from file: {file_path}")
            return False
    
    def is_duplicate_profile(self, profile, existing_profiles):
        """Check if a profile is a duplicate based on LinkedIn URL or other identifiers."""
        if not profile.get('linkedin_url'):
            return False
            
        for existing in existing_profiles:
            if existing.get('linkedin_url') == profile.get('linkedin_url'):
                return True
        return False
    
    def load_existing_profiles(self, file_path):
        """Load existing profiles from the output file to check for duplicates."""
        existing_profiles = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            profile = json.loads(line)
                            existing_profiles.append(profile)
            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON from existing file: {file_path}")
        return existing_profiles
    
    def save_profiles(self, output_file):
        """Save cleaned profiles by appending to a JSON file, avoiding duplicates."""
        try:
            # Load existing profiles to check for duplicates
            existing_profiles = self.load_existing_profiles(output_file)
            
            # Open file in append mode
            with open(output_file, 'a') as f:
                for profile in self.profiles:
                    # Skip if this profile is a duplicate
                    if not self.is_duplicate_profile(profile, existing_profiles):
                        json.dump(profile, f)
                        f.write('\n')
                        # Add to existing profiles to check against remaining profiles
                        existing_profiles.append(profile)
            
            logging.info(f"Profiles appended to: {output_file}")
        except Exception as e:
            logging.error(f"Error saving profiles: {e}")

    def clean_profile_urls(self):
        """Clean web.archive.org URLs from all profiles."""
        for profile in self.profiles:
            # Clean linkedin_url
            if 'linkedin_url' in profile:
                profile['linkedin_url'] = self.clean_url(profile['linkedin_url'])
            
            # Clean websites (could be a list or single URL)
            if 'websites' in profile:
                if isinstance(profile['websites'], list):
                    profile['websites'] = [self.clean_url(url) for url in profile['websites']]
                elif profile['websites']:
                    profile['websites'] = self.clean_url(profile['websites'])

class DorkGenerator:
    def __init__(self, api_key=None):
        openai.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
    def generate_dorks(self, query, profile_type="both"):
        """Generate search queries for finding LinkedIn profiles."""
        system_prompts = {
            "company": "You are a search dork generator specialized in finding LinkedIn company profiles.",
            "personal": "You are a search dork generator specialized in finding LinkedIn personal profiles.",
            "both": "You are a search dork generator specialized in finding both LinkedIn personal and company profiles."
        }
        
        prompt = f"""
        Generate 5 simple but effective search queries to find LinkedIn profiles related to: {query}

        Rules for the queries:
        1. Use simple terms that would appear in profiles
        2. Include 'site:linkedin.com' at the start
        3. For companies, include 'company' in the query
        4. For personal profiles, include relevant job titles

        6. Use quotes only for exact phrases
        7. Include location terms when relevant
        
        Return the response in this exact JSON format:
        [
            {{"dork": "site:linkedin.com medical spa owner", "explanation": "This query finds..."}}
        ]
        ## you must also use site:linkedin.com/in/ for personal profiles  dork query
        ## and also site:linkedin.com/company/ for company profiles dork query
        """

        try:
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompts[profile_type]},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            response_text = completion.choices[0].message['content'].strip()
            return json.loads(response_text)
        except Exception as e:
            logging.error(f"Error generating dorks: {str(e)}")
            return []

class LinkedInProfileScraper:
    def __init__(self):
        self.url = "https://search.hbubli.cc/search"  # Updated search endpoint
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'null',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()

    def search(self, query, pageno):
        """Search for LinkedIn profiles using the provided query."""
        logging.debug(f'Searching for query "{query}" on page {pageno}')

        # Format data exactly as in the curl request
        data_raw = f'q={query}&category_general=1&language=en&time_range=&safesearch=0&theme=simple'
        if pageno > 1:
            data_raw += f'&pageno={pageno}'

        try:
            # Add retry mechanism
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    response = self.session.post(
                        self.url,
                        headers=self.headers,
                        data=data_raw,
                        timeout=30,
                        allow_redirects=True
                    )
                    
                    if response.status_code == 200:
                        break
                    
                    retry_count += 1
                    if response.status_code == 429:  # Rate limit
                        wait_time = random.uniform(30, 60)
                        logging.warning(f"Rate limit hit, waiting {wait_time:.2f} seconds")
                        time.sleep(wait_time)
                    else:
                        time.sleep(random.uniform(5, 10))
                        
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        raise e
                    time.sleep(random.uniform(5, 10))

            if response.status_code != 200:
                logging.error(f'Received non-200 HTTP status code: {response.status_code}')
                return set()

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for results in both standard links and result titles
            links = soup.find_all("a", href=True)
            
            # Filter for LinkedIn profile URLs and clean them
            profile_links = set()
            for link in links:
                href = link.get("href", "").strip()
                if href and "linkedin.com" in href:
                    # Clean the URL to remove tracking parameters
                    cleaned_url = href.split('?')[0].split('#')[0]
                    # Ensure it's a profile URL and not a general LinkedIn page
                    if ('/in/' in cleaned_url or '/company/' in cleaned_url) and not any(x in cleaned_url for x in ['/pub/', '/jobs/', '/feed/', '/posts/']):
                        profile_links.add(cleaned_url)
            
            logging.debug(f'Found {len(profile_links)} LinkedIn profile links')
            return profile_links

        except requests.exceptions.Timeout:
            logging.error("Request timed out")
            time.sleep(random.uniform(10, 20))
            return set()
        except Exception as e:
            logging.error(f'Search error: {str(e)}')
            return set()

    def scrape_profiles(self, dork, max_pages=1):
        """Scrape LinkedIn profiles using the provided dork."""
        results = set()
        page = 1
        empty_pages = 0
        max_empty_pages = 2  # Stop after 2 consecutive empty pages

        while page <= max_pages and empty_pages < max_empty_pages:
            logging.info(f'Scraping page {page} for dork: {dork}')
            
            try:
                new_results = self.search(dork, page)
                
                if not new_results:
                    empty_pages += 1
                    logging.info(f'No results found on page {page}, empty pages: {empty_pages}')
                    if empty_pages >= max_empty_pages:
                        logging.info('Reached maximum empty pages, stopping search')
                        break
                else:
                    empty_pages = 0  # Reset counter when we find results
                    results.update(new_results)
                    logging.info(f'Found {len(new_results)} new profiles on page {page}. Total unique profiles: {len(results)}')
                
                # Adaptive delay based on response success
                delay = random.uniform(4, 8)
                if page % 5 == 0:  # Longer delay every 5 pages
                    delay = random.uniform(10, 15)
                if len(results) > 100:  # Even longer delay if we have many results
                    delay *= 1.5
                
                logging.debug(f'Waiting {delay:.2f} seconds before next request')
                time.sleep(delay)
                
                page += 1

            except Exception as e:
                logging.error(f'Error scraping page {page}: {str(e)}')
                time.sleep(random.uniform(10, 20))  # Wait longer on errors
                continue

        logging.info(f'Finished scraping after {page-1} pages. Found {len(results)} unique profiles')
        return results if results else set()  # Always return a set, even if empty

def main():
    # Initialize the profile manager
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("Please enter your OpenAI API key: ")
        os.environ['OPENAI_API_KEY'] = api_key

    manager = LinkedInProfileManager(api_key=api_key)

    # Get user input
    query = input("What kind of LinkedIn profiles are you looking for? ")
    profile_type = input("Type of profiles to search for (company/personal/both): ").lower()
    
    if profile_type not in ["company", "personal", "both"]:
        profile_type = "both"

    # Process profiles
    if manager.process_profiles(query, profile_type):
        print("\nProfile processing completed!")
        if manager.personal_profiles:
            print(f"Found {len(manager.personal_profiles)} personal profiles")
        if manager.company_profiles:
            print(f"Found {len(manager.company_profiles)} company profiles")
    else:
        print("Failed to process profiles")

    # Load profiles from the data file
    input_file = 'personal_profiles_data.json'
    manager.load_profiles(input_file)
    
    # Clean the URLs
    manager.clean_profile_urls()
    
    # Save the cleaned profiles
    output_file = 'personal_profiles_data_cleaned.json'
    manager.save_profiles(output_file)

if __name__ == "__main__":
    main() 