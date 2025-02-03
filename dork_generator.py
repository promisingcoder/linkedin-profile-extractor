import openai
import json
import os

class DorkGenerator:
    def __init__(self, api_key=None):
        # Use the provided API key or fallback to the environment variable.
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        openai.api_key = self.api_key

    def generate_dorks(self, query, profile_type="both"):
        """Generate Google dorks for finding LinkedIn profiles."""
        
        # Define the system prompt based on profile type.
        system_prompts = {
            "company": (
                "You are a search dork generator specialized in finding LinkedIn company profiles. "
                "Generate specific Google dorks that find company profiles on LinkedIn."
            ),
            "personal": (
                "You are a search dork generator specialized in finding LinkedIn personal profiles. "
                "Generate specific Google dorks that find personal profiles on LinkedIn."
            ),
            "both": (
                "You are a search dork generator specialized in finding LinkedIn profiles. "
                "Generate specific Google dorks that find both personal and company profiles on LinkedIn."
            )
        }

        # Create the prompt for the specific use case.
        prompt = f"""
Generate 5 Google dorks to find LinkedIn profiles related to: {query}

Rules for the dorks:
1. Always include 'site:linkedin.com'
2. Use intitle:, inurl:, OR, AND operators where appropriate.
3. For companies, include 'company' or 'business' in the search.
4. For personal profiles, include '/in/' in the site:.
5. Format each dork on a new line.
6. For company profile , include '/company/' in the site:.

Return only a valid JSON array (without any additional text or markdown) in this exact format:
[
    {{"dork": "site:linkedin.com...", "explanation": "This dork finds..."}},
    {{"dork": "site:linkedin.com...", "explanation": "This dork finds..."}}
]
"""

        try:
            # Call the OpenAI Chat Completion API.
            response = openai.ChatCompletion.create(
                model="gpt-4",  # You can change this to "gpt-3.5-turbo" if needed.
                messages=[
                    {"role": "system", "content": system_prompts[profile_type]},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            # Get the response text.
            response_text = response.choices[0].message.content.strip()
            print("Raw API response:")
            print(response_text)

            # Attempt to parse the response as JSON.
            try:
                dorks = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback: Parse the output manually if strict JSON is not returned.
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
            print(f"Error generating dorks: {str(e)}")
            return []

    def save_dorks_to_file(self, dorks, filename="linkedin_dorks.txt"):
        """Save generated dorks to a file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for dork in dorks:
                    f.write(f"# {dork.get('explanation', 'No explanation provided')}\n")
                    f.write(f"{dork.get('dork', '')}\n\n")
            print(f"Dorks saved to {filename}")
        except Exception as e:
            print(f"Error saving dorks to file: {str(e)}")

def main():
    # Initialize the dork generator with the API key.
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        api_key = input("Please enter your OpenAI API key: ")
        os.environ['OPENAI_API_KEY'] = api_key

    generator = DorkGenerator(api_key=api_key)

    # Get user input.
    query = input("What kind of LinkedIn profiles are you looking for? ")
    profile_type = input("Type of profiles to search for (company/personal/both): ").lower()

    # Validate profile type.
    if profile_type not in ["company", "personal", "both"]:
        profile_type = "both"

    # Generate dorks.
    print("\nGenerating dorks...")
    dorks = generator.generate_dorks(query, profile_type)

    if not dorks:
        print("No dorks were generated. Please try again.")
        return

    # Print the generated dorks.
    print("\nGenerated Dorks:")
    print("-" * 50)
    for dork in dorks:
        print(f"\n# {dork.get('explanation', 'No explanation provided')}")
        print(dork.get('dork', ''))

    # Save the dorks to a file.
    generator.save_dorks_to_file(dorks)

if __name__ == "__main__":
    main()
