import requests
from bs4 import BeautifulSoup
import time
import logging
import random
import json
import os
from openai import OpenAI
from browser_module.browser import Browser, HeadlessBrowser
import re
from ai_module.linkedin_ai_agent import LinkedInAIAgent, ProfileType
from search_module.integrated_linkedin_scraper import LinkedInProfileScraper
from search_module.searxng_search import SearxNGSearch
from ai_module.dork_generator import DorkGenerator
import sys

def get_openai_api_key():
    """Get OpenAI API key from environment variables, .env file, or user input."""
    def is_valid_api_key(key):
        """Test if the API key is valid by making a test API call."""
        if not key or not isinstance(key, str):
            return False
        
        # Check if it's not the placeholder key from .env
        if 'your_openai_api_key_here' in key or 'your_' in key:
            return False
            
        # Basic format check
        if not key.startswith('sk-') or len(key) <= 20:
            return False
            
        # Test the key with a minimal API call
        try:
            client = OpenAI(api_key=key)
            # Make a minimal test request
            client.models.list()
            return True
        except Exception as e:
            logging.warning(f"API key validation failed: {str(e)}")
            return False

    def prompt_for_api_key():
        """Prompt user for API key and validate it."""
        print("\nOpenAI API key not found or invalid.")
        while True:
            try:
                api_key = input("Please enter your OpenAI API key (or 'q' to quit): ").strip()
                if api_key.lower() == 'q':
                    raise KeyboardInterrupt("User chose to quit")
                
                if is_valid_api_key(api_key):
                    return api_key
                    
                print("Invalid API key. Please ensure your key is correct and your account is active.")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.error(f"Error validating API key: {e}")
                print("An error occurred while validating the API key. Please try again.")

    try:
        # Try getting key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv('OPENAI_API_KEY')
            except ImportError:
                logging.warning("python-dotenv not installed. Using environment variables only.")
            except Exception as e:
                logging.error(f"Error loading .env file: {e}")

        # Validate the API key
        if not is_valid_api_key(api_key):
            api_key = prompt_for_api_key()

        # Save to environment variable for current session
        os.environ['OPENAI_API_KEY'] = api_key

        # Ask to save to .env file
        try:
            save_to_env = input("Would you like to save the API key to .env file? (y/n): ").lower()
            if save_to_env == 'y':
                try:
                    # Read existing .env file
                    env_lines = []
                    api_key_exists = False
                    
                    if os.path.exists('.env'):
                        with open('.env', 'r') as f:
                            env_lines = f.readlines()
                            
                    # Update or add the API key
                    for i, line in enumerate(env_lines):
                        if line.strip().startswith('OPENAI_API_KEY='):
                            env_lines[i] = f'OPENAI_API_KEY={api_key}\n'
                            api_key_exists = True
                            break
                    
                    if not api_key_exists:
                        env_lines.append(f'\nOPENAI_API_KEY={api_key}\n')
                    
                    # Write back to .env file
                    with open('.env', 'w') as f:
                        f.writelines(env_lines)
                    print("API key saved to .env file.")
                except Exception as e:
                    logging.error(f"Error saving API key to .env file: {e}")
                    print("Failed to save API key to .env file. Continuing with current session only.")
        except KeyboardInterrupt:
            print("\nSkipping .env file save. Continuing with current session only.")

        return api_key

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error getting API key: {e}")
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

def get_search_config():
    """Get search configuration from environment variables or .env file."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logging.warning("python-dotenv not installed. Using environment variables only.")
    
    # Get search method, default to searxng
    search_method = os.getenv('SEARCH_METHOD', 'searxng').lower()
    
    return {
        'method': search_method
    }

# Constants for directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROFILES_DIR = os.path.join(DATA_DIR, "profiles")
QUERIES_DIR = os.path.join(DATA_DIR, "queries")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
COOKIES_DIR = os.path.join(DATA_DIR, "cookies")
INSTRUCTIONS_DIR = os.path.join(BASE_DIR, "instructions")

# Create directories if they don't exist
for directory in [DATA_DIR, PROFILES_DIR, QUERIES_DIR, LOGS_DIR, COOKIES_DIR, INSTRUCTIONS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Constants for files
COOKIES_FILE = os.path.join(COOKIES_DIR, "cookies.txt")
PERSONAL_INSTRUCTIONS_FILE = os.path.join(INSTRUCTIONS_DIR, "linkedin_profile_instructions.txt")
COMPANY_INSTRUCTIONS_FILE = os.path.join(INSTRUCTIONS_DIR, "company_profile_instructions.txt")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, f'linkedin_scraper_{time.strftime("%Y%m%d_%H%M%S")}.log')),
        logging.StreamHandler()
    ]
)

class ProfileType:
    PERSONAL = "personal"
    COMPANY = "company"

class LinkedInProfileManager:
    def __init__(self, api_key=None):
        self.api_key = api_key or get_openai_api_key()
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Get search configuration
        self.search_config = get_search_config()
        logging.info(f"Using search method: {self.search_config['method']}")
        
        # Initialize search module based on configuration
        if self.search_config['method'] == 'searxng':
            self.searx_search = SearxNGSearch()
            logging.info(f"Using {len(self.searx_search.search_engines)} SearxNG instances for searching")
        else:
            logging.warning(f"Search method '{self.search_config['method']}' not implemented, falling back to SearxNG")
            self.searx_search = SearxNGSearch()
            
        self.scraper = LinkedInProfileScraper()
        self.ai_agent = LinkedInAIAgent(api_key=self.api_key)
        self.browser = None
        
        # Initialize separate sets for different profile types
        self.personal_profiles = set()
        self.company_profiles = set()
        
        self.profiles = []

    def process_profiles(self, query, profile_type="both"):
        """Main method to process LinkedIn profiles"""
        # Set up AI agent
        self.ai_agent.set_query(query)
        
        if profile_type == "both":
            # Handle both profile types
            self.ai_agent.set_profile_type(ProfileType.PERSONAL)
            personal_results = self.ai_agent.generate_search_queries()
            
            self.ai_agent.set_profile_type(ProfileType.COMPANY)
            company_results = self.ai_agent.generate_search_queries()
            
            # Combine queries
            all_queries = personal_results['queries'] + company_results['queries']
        else:
            # Handle single profile type
            self.ai_agent.set_profile_type(profile_type)
            results = self.ai_agent.generate_search_queries()
            all_queries = results['queries']
        
        # Save generated queries
        queries_file = os.path.join(QUERIES_DIR, f'generated_dorks_{time.strftime("%Y%m%d_%H%M%S")}.txt')
        with open(queries_file, 'w') as f:
            for query in all_queries:
                f.write(f"{query}\n")

        # Search for profiles using each query
        for query in all_queries:
            logging.info(f"Processing search query: {query}")
            personal_results, company_results = self.searx_search.search_profiles(query)
            self.personal_profiles.update(personal_results)
            self.company_profiles.update(company_results)
            # Add random delay between searches
            time.sleep(random.uniform(2, 5))

        # Save categorized profiles
        self.save_categorized_profiles()
        
        # Process profiles with appropriate instructions
        self.process_with_instructions()
        
        return True

    def save_categorized_profiles(self):
        """Save personal and company profiles to separate files"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        if self.personal_profiles:
            personal_file = os.path.join(PROFILES_DIR, f'personal_profiles_{timestamp}.txt')
            with open(personal_file, 'w') as f:
                for profile in self.personal_profiles:
                    f.write(f"{profile}\n")
            logging.info(f"Saved {len(self.personal_profiles)} personal profiles to {personal_file}")

        if self.company_profiles:
            company_file = os.path.join(PROFILES_DIR, f'company_profiles_{timestamp}.txt')
            with open(company_file, 'w') as f:
                for profile in self.company_profiles:
                    f.write(f"{profile}\n")
            logging.info(f"Saved {len(self.company_profiles)} company profiles to {company_file}")

    def process_with_instructions(self):
        """Process profiles with appropriate instructions"""
        try:
            # Initialize browser if not already initialized
            if not self.browser:
                self.browser = Browser()
                
            # Ensure logged in with cookies
            if not self.browser.ensure_logged_in(COOKIES_FILE):
                logging.error("Failed to ensure login status")
                    return False

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            current_batch_file = os.path.join(PROFILES_DIR, "current_batch_profiles.txt")

            # Process personal profiles
            if self.personal_profiles:
                # Create a batch file for processing
                with open(current_batch_file, 'w') as f:
                    for profile in self.personal_profiles:
                        f.write(f"{profile}\n")
                
                # Execute personal profile instructions
                self.browser.execute_instructions(PERSONAL_INSTRUCTIONS_FILE)
                
            # Process company profiles
            if self.company_profiles:
                # Create a batch file for processing
                with open(current_batch_file, 'w') as f:
                    for profile in self.company_profiles:
                        f.write(f"{profile}\n")
                
                # Execute company profile instructions
                self.browser.execute_instructions(COMPANY_INSTRUCTIONS_FILE)

            # Clean up temporary batch file
            if os.path.exists(current_batch_file):
                os.remove(current_batch_file)

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
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        if self.personal_profiles:
            filename = os.path.join(PROFILES_DIR, f'unprocessed_personal_profiles_{timestamp}.txt')
            with open(filename, 'w') as f:
                for profile in self.personal_profiles:
                    f.write(f"{profile}\n")
            logging.info(f"Saved unprocessed personal profiles to {filename}")
            
        if self.company_profiles:
            filename = os.path.join(PROFILES_DIR, f'unprocessed_company_profiles_{timestamp}.txt')
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
            # Ensure output file is in the profiles directory
            output_path = os.path.join(PROFILES_DIR, output_file)
            
            # Load existing profiles to check for duplicates
            existing_profiles = self.load_existing_profiles(output_path)
            
            # Open file in append mode
            with open(output_path, 'a') as f:
                for profile in self.profiles:
                    # Skip if this profile is a duplicate
                    if not self.is_duplicate_profile(profile, existing_profiles):
                        json.dump(profile, f)
                        f.write('\n')
                        # Add to existing profiles to check against remaining profiles
                        existing_profiles.append(profile)
            
            logging.info(f"Profiles appended to: {output_path}")
        except Exception as e:
            logging.error(f"Error saving profiles: {e}")

def main():
    try:
        # Get OpenAI API key
        api_key = get_openai_api_key()
    if not api_key:
            print("Error: OpenAI API key is required to proceed.")
            return

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
        input_file = os.path.join(PROFILES_DIR, 'personal_profiles_data.json')
    manager.load_profiles(input_file)
    
    # Save the cleaned profiles
    output_file = 'personal_profiles_data_cleaned.json'
    manager.save_profiles(output_file)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 