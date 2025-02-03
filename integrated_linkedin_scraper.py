import requests
from bs4 import BeautifulSoup
import time
import logging
import random
import json
import os
import openai

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DorkGenerator:
    def __init__(self, api_key=None):
        # Set the API key for the openai module
        openai.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
    def generate_dorks(self, query, profile_type="both"):
        """Generate Google dorks for finding LinkedIn profiles."""
        
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
        5. Keep operators simple (avoid complex AND/OR)
        6. Use quotes only for exact phrases
        7. Include location terms when relevant
        
        Return the response in this exact JSON format:
        [
            {{"dork": "site:linkedin.com medical spa owner", "explanation": "This query finds..."}}
        ]
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
            logging.debug(f"Raw GPT response: {response_text}")
            
            try:
                dorks = json.loads(response_text)
            except json.JSONDecodeError:
                logging.warning("Failed to parse JSON response, attempting manual parsing")
                lines = response_text.split('\n')
                dorks = []
                current_dork = None
                current_explanation = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('site:linkedin.com'):
                        if current_dork and current_explanation:
                            dorks.append({"dork": current_dork, "explanation": current_explanation})
                        current_dork = line
                        current_explanation = None
                    elif line and current_dork and not current_explanation:
                        current_explanation = line
                
                if current_dork and current_explanation:
                    dorks.append({"dork": current_dork, "explanation": current_explanation})
            
            return dorks

        except Exception as e:
            logging.error(f"Error generating dorks: {str(e)}")
            return []

class LinkedInProfileScraper:
    def __init__(self):
        self.url = "https://priv.au/search"
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
        self.session = requests.Session()

    def search(self, query, pageno):
        logging.debug(f'Searching for query "{query}" on page {pageno}')

        # Remove complex operators from query
        simplified_query = query.replace(' AND ', ' ').replace(' OR ', ' ')
        
        data = {
            'q': simplified_query,
            'category_general': '1',
            'language': 'en',
            'time_range': '',
            'safesearch': '1',
            'theme': 'simple',
            'pageno': str(pageno)
        }

        try:
            # Add retry mechanism
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    response = self.session.post(
                        self.url,
                        headers=self.headers,
                        data=data,
                        timeout=30,
                        allow_redirects=True
                    )
                    break
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        raise e
                    time.sleep(random.uniform(5, 10))

            logging.debug(f'Response status code: {response.status_code}')

            if response.status_code != 200:
                logging.error(f'Received non-200 HTTP status code: {response.status_code}')
                if response.status_code == 429:
                    logging.warning("Rate limit hit, waiting longer before next request")
                    time.sleep(random.uniform(30, 60))
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            
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
            return []
        except Exception as e:
            logging.error(f'Search error: {str(e)}')
            return []

    def scrape_profiles(self, dork, max_pages=50):
        results = set()
        page = 1
        empty_pages = 0
        max_empty_pages = 3  # Allow more empty pages before stopping

        while page <= max_pages and empty_pages < max_empty_pages:
            logging.info(f'Scraping page {page} for dork: {dork}')
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

        logging.info(f'Finished scraping after {page-1} pages. Found {len(results)} unique profiles')
        return results

def save_links_to_file(links, filename):
    logging.info(f'Saving {len(links)} links to {filename}')
    try:
        with open(filename, 'w') as file:
            for link in links:
                file.write(f"{link}\n")
        logging.info(f'Successfully saved links to {filename}')
    except Exception as e:
        logging.error(f'Error saving links: {e}')

def main():
    # Initialize the dork generator
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("Please enter your OpenAI API key: ")
        os.environ['OPENAI_API_KEY'] = api_key

    generator = DorkGenerator(api_key=api_key)
    scraper = LinkedInProfileScraper()

    # Get user input
    query = input("What kind of LinkedIn profiles are you looking for? ")
    profile_type = input("Type of profiles to search for (company/personal/both): ").lower()
    
    if profile_type not in ["company", "personal", "both"]:
        profile_type = "both"

    # Generate dorks
    print("\nGenerating search queries...")
    dorks = generator.generate_dorks(query, profile_type)

    if not dorks:
        print("No search queries were generated. Please try again.")
        return

    # Save dorks to file
    with open("generated_dorks.txt", 'w') as f:
        for dork in dorks:
            f.write(f"# {dork.get('explanation', 'No explanation provided')}\n")
            f.write(f"{dork.get('dork', '')}\n\n")

    # Scrape profiles using each dork
    all_profiles = set()
    for dork in dorks:
        print(f"\nProcessing search query: {dork['dork']}")
        profiles = scraper.scrape_profiles(dork['dork'])
        all_profiles.update(profiles)
        time.sleep(random.uniform(3, 7))  # Delay between different dorks

    # Save results
    if all_profiles:
        save_links_to_file(all_profiles, "linkedin_profiles.txt")
        print(f"\nFound {len(all_profiles)} unique LinkedIn profiles")
        print("Results have been saved to 'linkedin_profiles.txt'")
    else:
        print("No profiles were found")

if __name__ == "__main__":
    main() 