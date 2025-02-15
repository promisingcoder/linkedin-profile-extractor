import os
import sys
import logging
from dotenv import load_dotenv
import time

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_module.browser import Browser

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def test_login():
    """Test LinkedIn login functionality."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get LinkedIn credentials
        linkedin_email = os.getenv('LINKEDIN_EMAIL')
        linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        
        if not linkedin_email or not linkedin_password:
            logging.error("LinkedIn credentials not found in environment variables")
            return False
            
        # Initialize browser
        browser = None
        try:
            logging.info("Initializing browser...")
            browser = Browser()
            
            # Create cookies directory if it doesn't exist
            cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cookies")
            os.makedirs(cookies_dir, exist_ok=True)
            cookies_file = os.path.join(cookies_dir, "cookies.txt")
            
            # Test login
            logging.info("Testing login...")
            if browser.ensure_logged_in(cookies_file):
                logging.info("Login successful!")
                
                # Verify login status
                if browser.is_logged_in():
                    logging.info("Login verification successful!")
                    return True
                else:
                    logging.error("Login verification failed!")
                    return False
            else:
                logging.error("Login failed!")
                return False
                
        except Exception as e:
            logging.error(f"Error during login test: {str(e)}")
            return False
        finally:
            if browser:
                logging.info("Closing browser...")
                browser.close()
                
    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        return False

def main():
    """Main function to run the login test."""
    try:
        print("\nStarting LinkedIn login test...")
        if test_login():
            print("\nLogin test passed successfully! ✅")
            sys.exit(0)
        else:
            print("\nLogin test failed! ❌")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 