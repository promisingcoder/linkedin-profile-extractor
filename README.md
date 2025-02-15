# LinkedIn Profile Extractor

## Overview

**LinkedIn Profile Extractor** is a Python-based tool designed to automate the process of scraping LinkedIn profiles using a headless browser. The extractor gathers essential information from LinkedIn profiles, including the user's name, headline, current company, location, LinkedIn URL, and any associated websites. The data is then stored in a JSON file for further use or analysis.

The project leverages `undetected-chromedriver` to bypass LinkedIn's bot detection mechanisms and uses `selenium` to control browser actions. It also integrates with OpenAI's API for intelligent profile processing and search query generation.

## Features

- **Automated Profile Scraping**: 
  - Efficiently scrape LinkedIn profiles while respecting rate limits
  - Automatic retry mechanisms for failed requests
  - Smart delay management between requests

- **Intelligent Search**: 
  - AI-powered search query generation using OpenAI's API
  - Support for both personal and company profiles
  - Advanced dork generation for precise targeting

- **Multi-Instance Search**: 
  - Utilizes multiple SearxNG instances for robust searching
  - Fallback mechanisms when search instances fail
  - Automatic rotation between search engines

- **Smart Authentication**: 
  - Secure handling of LinkedIn credentials
  - Automatic cookie management with save/load functionality
  - Persistent session handling
  - Automatic re-login when cookies expire

- **Robust API Key Management**:
  - Secure OpenAI API key handling
  - Multiple key storage options:
    - Environment variables
    - .env file
    - Interactive key input
  - Automatic key validation
  - Secure key storage with user consent

- **Profile Categorization**: 
  - Separate handling of personal and company profiles
  - Intelligent profile type detection
  - Category-specific data extraction

- **Data Management**:
  - Automatic deduplication of profiles
  - JSON-based data storage
  - Structured data organization
  - Backup of unprocessed profiles

- **Error Recovery**: 
  - Comprehensive error handling
  - Automatic retry mechanisms
  - Session recovery
  - Progress saving during interruptions

## Project Structure

```
linkedin_profile_extractor/
│
├── browser_module/            # Browser automation
│   ├── __init__.py
│   ├── browser.py            # Main browser control
│   └── utils/                # Browser utilities
│       ├── __init__.py
│       ├── click_element_by_selector.py
│       ├── fill_input.py
│       ├── find_element_by_xpath.py
│       ├── get_attribute_value.py
│       ├── get_inner_text.py
│       ├── load_cookies.py
│       └── save_cookies.py
│
├── search_module/            # Search functionality
│   ├── __init__.py
│   ├── integrated_linkedin_scraper.py
│   └── searxng_search.py
│
├── ai_module/               # AI integration
│   ├── __init__.py
│   ├── linkedin_ai_agent.py
│   ├── dork_generator.py
│   └── instruction_generator.py
│
├── data/                    # Data storage
│   ├── profiles/           # Profile data
│   ├── queries/            # Search queries
│   ├── logs/              # Application logs
│   └── cookies/           # Browser cookies
│
├── instructions/           # Scraping instructions
│   ├── linkedin_profile_instructions.txt
│   └── company_profile_instructions.txt
│
├── tests/                  # Test suite
│   ├── __init__.py
│   └── test_login.py      # Login testing
│
├── linkedin_profile_manager.py  # Main application
├── requirements.txt            # Dependencies
└── .env                       # Configuration
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/promisingcoder/linkedin-profile-extractor.git
   cd linkedin-profile-extractor
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   Create a `.env` file:
   ```env
   # LinkedIn Credentials
   LINKEDIN_EMAIL=your.email@example.com
   LINKEDIN_PASSWORD=your_linkedin_password

   # OpenAI API Key
   OPENAI_API_KEY=your_openai_api_key

   # Search Configuration
   SEARCH_METHOD=searxng
   ```

4. **API Key Setup:**
   The application supports multiple ways to provide your OpenAI API key:
   - Environment variables
   - .env file
   - Interactive prompt with validation
   
   The key will be validated before use and stored securely.

## Usage

1. **Run the main script:**
   ```bash
   python linkedin_profile_manager.py
   ```

2. **First Run Setup:**
   - Validates OpenAI API key
   - Handles LinkedIn authentication
   - Creates necessary directories
   - Sets up logging

3. **Profile Search:**
   - Enter your search query (e.g., "Med Spa Owners in California")
   - Choose profile type (personal/company/both)
   - Wait for AI-generated search queries
   - Monitor progress in logs

4. **Data Storage:**
   - Profiles: `data/profiles/`
   - Logs: `data/logs/`
   - Cookies: `data/cookies/`
   - Search queries: `data/queries/`

## Error Handling

The application includes comprehensive error handling for:
- Network issues
- Authentication failures
- Rate limiting
- API key validation
- File operations
- User interruptions
- Session management

## Security

- Secure credential management
- No hardcoded secrets
- Environment-based configuration
- Secure cookie handling
- Local data storage
- Session isolation

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Key test areas:
- Login functionality
- Cookie management
- API key validation
- Profile scraping
- Search functionality

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
