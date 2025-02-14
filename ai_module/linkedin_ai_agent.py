from openai import OpenAI
import json
import os
import logging
from typing import List, Dict, Optional, Union
from enum import Enum
import time

# Constants
INSTRUCTIONS_DIR = "instructions"
PERSONAL_INSTRUCTIONS_FILE = os.path.join(INSTRUCTIONS_DIR, "linkedin_profile_instructions.txt")
COMPANY_INSTRUCTIONS_FILE = os.path.join(INSTRUCTIONS_DIR, "company_profile_instructions.txt")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProfileType(Enum):
    PERSONAL = "personal"
    COMPANY = "company"

class LinkedInAIAgent:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LinkedIn AI Agent with OpenAI API key."""
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.profile_type = None
        self.query = None

    def _get_personal_profile_prompt(self) -> str:
        """Get the system prompt for personal profile search."""
        return """You are an AI agent specialized in generating search queries for LinkedIn personal profiles.
        Your task is to create effective search queries that will find relevant personal profiles on LinkedIn.

        Rules for generating queries:
        1. ALWAYS include 'site:linkedin.com/in/' in EVERY query
        2. Focus on professional titles, skills, and industry-specific terms
        3. Use location qualifiers when relevant
        4. Include relevant certifications or qualifications
        5. Consider company names or industry leaders
        6. Use quotes for exact phrases when necessary

        Return a JSON object with:
        - queries: list of search queries
        - explanations: list of explanations for each query
        - suggested_filters: additional filtering suggestions
        """

    def _get_company_profile_prompt(self) -> str:
        """Get the system prompt for company profile search."""
        return """You are an AI agent specialized in generating search queries for LinkedIn company profiles.
        Your task is to create effective search queries that will find relevant company profiles on LinkedIn.

        Rules for generating queries:
        1. ALWAYS include 'site:linkedin.com/company/' in EVERY query
        2. Focus on industry terms, company types, and business categories
        3. Use location qualifiers when relevant
        4. Include relevant business classifications
        5. Consider company size and type indicators
        6. Use quotes for exact phrases when necessary

        Return a JSON object with:
        - queries: list of search queries
        - explanations: list of explanations for each query
        - suggested_filters: additional filtering suggestions
        """

    def set_profile_type(self, profile_type: Union[str, ProfileType]) -> None:
        """Set the profile type for the search."""
        if isinstance(profile_type, str):
            profile_type = ProfileType(profile_type.lower())
        self.profile_type = profile_type

    def set_query(self, query: str) -> None:
        """Set the search query."""
        self.query = query

    def generate_search_queries(self) -> Dict:
        """Generate search queries based on profile type and user query."""
        if not self.profile_type or not self.query:
            raise ValueError("Profile type and query must be set before generating search queries")

        # Select appropriate prompt based on profile type
        system_prompt = (
            self._get_personal_profile_prompt()
            if self.profile_type == ProfileType.PERSONAL
            else self._get_company_profile_prompt()
        )

        user_prompt = f"""
        Generate 5 effective search queries for finding {self.profile_type.value} LinkedIn profiles related to: {self.query}

        Requirements:
        1. Each query must be specific and targeted
        2. Include relevant industry terms
        3. Consider geographical aspects if relevant
        4. Use appropriate filters and operators
        5. Ensure high precision in results

        Return the response in this exact JSON format:
        {{
            "queries": [
                "site:linkedin.com/{self.profile_type.value == ProfileType.PERSONAL.value and 'in' or 'company'}/example-query",
                ...
            ],
            "explanations": [
                "This query targets...",
                ...
            ],
            "suggested_filters": [
                "Filter by...",
                ...
            ]
        }}
        """

        try:
            completion = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            response = json.loads(completion.choices[0].message.content)
            return response

        except Exception as e:
            logging.error(f"Error generating search queries: {e}")
            raise

    def get_instruction_file(self) -> str:
        """Get the appropriate instruction file based on profile type."""
        if self.profile_type == ProfileType.PERSONAL:
            return PERSONAL_INSTRUCTIONS_FILE
        return COMPANY_INSTRUCTIONS_FILE

    def process_results(self, results: List[str], output_file: str) -> None:
        """Process the search results and save them to a file."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{output_file}_{timestamp}.txt"
        
        try:
            with open(filename, 'w') as f:
                for result in results:
                    f.write(f"{result}\n")
            logging.info(f"Results saved to {filename}")
            
        except Exception as e:
            logging.error(f"Error saving results: {e}")
            raise

def main():
    # Get API key from environment or user input
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("Please enter your OpenAI API key: ")
        os.environ['OPENAI_API_KEY'] = api_key

    # Initialize the AI agent
    agent = LinkedInAIAgent(api_key)

    # Get profile type from user
    while True:
        profile_type = input("Enter profile type (personal/company): ").lower()
        if profile_type in ['personal', 'company']:
            break
        print("Invalid profile type. Please enter 'personal' or 'company'.")

    # Set profile type
    agent.set_profile_type(profile_type)

    # Get search query from user
    query = input("Enter your search query: ")
    agent.set_query(query)

    try:
        # Generate search queries
        results = agent.generate_search_queries()
        
        print("\nGenerated Search Queries:")
        print("-" * 50)
        for i, (query, explanation) in enumerate(zip(results['queries'], results['explanations']), 1):
            print(f"\n{i}. Query: {query}")
            print(f"   Explanation: {explanation}")

        print("\nSuggested Filters:")
        for filter_suggestion in results['suggested_filters']:
            print(f"- {filter_suggestion}")

        # Get instruction file
        instruction_file = agent.get_instruction_file()
        print(f"\nUsing instruction file: {instruction_file}")

        # Save results
        agent.process_results(results['queries'], f"linkedin_{profile_type}_queries")

    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 