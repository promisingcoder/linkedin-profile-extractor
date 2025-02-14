# LinkedIn Profile Extractor

## Overview

**LinkedIn Profile Extractor** is a Python-based tool designed to automate the process of scraping LinkedIn profiles using a headless browser. The extractor gathers essential information from LinkedIn profiles, including the user's name, headline, current company, location, LinkedIn URL, and any associated websites. The data is then stored in a CSV file for further use or analysis.

The project leverages `undetected-chromedriver` to bypass LinkedIn's bot detection mechanisms and uses `selenium` to control browser actions.

## Project Structure

```
linkedin_profile_extractor/
│
├── browser_module/            # Module containing browser-related functionality
│   ├── __init__.py           # Browser module initialization
│   ├── browser.py            # Main browser interaction logic
│   └── utils/                # Browser utilities
│       ├── __init__.py
│       ├── click_element_by_selector.py
│       ├── fill_input.py
│       ├── find_element_by_xpath.py
│       ├── get_attribute_value.py
│       └── get_inner_text.py
│
├── search_module/            # Module for search functionality
│   ├── __init__.py
│   ├── integrated_linkedin_scraper.py
│   └── searxng_search.py
│
├── ai_module/               # AI-powered functionality
│   ├── __init__.py
│   ├── linkedin_ai_agent.py
│   ├── dork_generator.py
│   └── instruction_generator.py
│
├── instructions/           # Directory containing scraping instructions
│   ├── linkedin_profile_instructions.txt
│   └── company_profile_instructions.txt
│
├── linkedin_profile_manager.py  # Main script for managing profile extraction
├── requirements.txt            # Project dependencies
└── cookies.txt                # Cookies file to maintain session
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/promisingcoder/linkedin-profile-extractor.git
   cd linkedin-profile-extractor
   ```

2. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the environment:**
   - Ensure that you have Chrome installed on your system.
   - The script uses undetected-chromedriver to automatically install the appropriate ChromeDriver version.
   - Set your OpenAI API key in the environment variables:
     ```bash
     export OPENAI_API_KEY='your-api-key-here'
     ```

4. **Usage:**
   Run the main script:
   ```bash
   python linkedin_profile_manager.py
   ```
   The script will:
   - Ask for your search query (e.g., "Med Spa Owners in California")
   - Ask for profile type (personal/company/both)
   - Generate appropriate search queries using AI
   - Search for and collect LinkedIn profile URLs
   - Scrape the profiles and save the data

5. **Cookies:**
   - The `Browser` class handles cookie management.
   - Cookies are automatically loaded from `cookies.txt` if available.
   - You may need to manually save your LinkedIn cookies to `cookies.txt` for authentication.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! If you find any bugs or have suggestions for improvements, please create an issue or submit a pull request.
