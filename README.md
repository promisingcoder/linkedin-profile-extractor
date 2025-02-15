# LinkedIn Profile Extractor

## Overview

**LinkedIn Profile Extractor** is a Python-based tool designed to automate the process of scraping LinkedIn profiles using a headless browser. The extractor gathers essential information from LinkedIn profiles, including the user's name, headline, current company, location, LinkedIn URL, and any associated websites. The data is then stored in a JSON file for further use or analysis.

The project leverages `undetected-chromedriver` to bypass LinkedIn's bot detection mechanisms and uses `selenium` to control browser actions. It also integrates with OpenAI's API for intelligent profile processing and search query generation.

## Features

- **Automated Profile Scraping**: Efficiently scrape LinkedIn profiles while respecting rate limits
- **Intelligent Search**: AI-powered search query generation using OpenAI's API
- **Multi-Instance Search**: Utilizes multiple SearxNG instances for robust searching
- **Smart Authentication**: 
  - Secure handling of LinkedIn credentials
  - Automatic cookie management
  - Session persistence
- **Robust API Key Management**:
  - Secure OpenAI API key handling
  - Automatic key validation
  - Support for environment variables and .env file
  - Interactive key input with validation
- **Profile Categorization**: Separate handling of personal and company profiles
- **Data Deduplication**: Prevents duplicate profile processing
- **Error Recovery**: Saves progress and handles interruptions gracefully

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
├── data/                    # Data storage directory
│   ├── profiles/           # Scraped profile data
│   ├── queries/            # Generated search queries
│   ├── logs/              # Application logs
│   └── cookies/           # Browser cookies
│
├── instructions/           # Directory containing scraping instructions
│   ├── linkedin_profile_instructions.txt
│   └── company_profile_instructions.txt
│
├── linkedin_profile_manager.py  # Main script for managing profile extraction
├── requirements.txt            # Project dependencies
└── .env                       # Environment configuration file
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
   Create a `.env` file in the root directory with the following content:
   ```env
   # LinkedIn Credentials
   LINKEDIN_EMAIL=your.email@example.com
   LINKEDIN_PASSWORD=your_linkedin_password

   # OpenAI API Key
   OPENAI_API_KEY=your_openai_api_key

   # Search Configuration
   SEARCH_METHOD=searxng  # Options: searxng, google, bing, duckduckgo
   ```

4. **API Key Setup:**
   The script supports multiple ways to provide your OpenAI API key:
   - Environment variables
   - .env file
   - Interactive prompt
   
   The key will be validated before use to ensure it's active and correct.

5. **Usage:**
   Run the main script:
   ```bash
   python linkedin_profile_manager.py
   ```
   The script will:
   - Validate your OpenAI API key
   - Ask for your search query (e.g., "Med Spa Owners in California")
   - Ask for profile type (personal/company/both)
   - Generate appropriate search queries using AI
   - Search for and collect LinkedIn profile URLs
   - Scrape the profiles and save the data

6. **Data Storage:**
   - Scraped profiles are saved in the `data/profiles` directory
   - Logs are stored in `data/logs`
   - Cookies are managed in `data/cookies`
   - Search queries are saved in `data/queries`

## Error Handling

The script includes robust error handling for:
- Invalid or expired API keys
- Network connectivity issues
- Rate limiting
- Invalid credentials
- File system operations
- Keyboard interrupts

## Security Notes

- API keys and credentials are never hardcoded
- Sensitive data is stored in .env file (not committed to version control)
- Cookies are stored securely for session management
- All data is stored locally on your machine

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! If you find any bugs or have suggestions for improvements, please create an issue or submit a pull request.
