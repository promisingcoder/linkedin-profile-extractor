import undetected_chromedriver as uc  # Import the undetected_chromedriver module to evade detection
from time import sleep  # Import sleep function to add delays
import chromedriver_autoinstaller  # Import to ensure the correct chromedriver version is installed
from .utils.click_element_by_selector import click_element_by_selector  # Import custom function to click elements
from .utils.fill_input import fill_input  # Import custom function to fill input fields
from .utils.load_cookies import load_cookies  # Import custom function to load browser cookies
from .utils.save_cookies import save_cookies  # Import custom function to save browser cookies
from .utils.get_attribute_value import get_attribute_value  # Import custom function to get attribute values
from .utils.get_inner_text import get_inner_text  # Import custom function to get inner text of elements
from .utils.find_element_by_xpath import find_element_by_xpath, find_elements_by_xpath  # Import custom function to find elements
import os  # Import OS module for operating system functionality
from selenium.webdriver.support.ui import WebDriverWait  # Import for explicit waits
from selenium.webdriver.support import expected_conditions as EC  # Import expected conditions for waits
from selenium.webdriver.common.by import By  # Import for element location strategies
import logging  # Import logging module
import shutil  # Import to perform high-level file operations
import csv  # Import CSV module to read and write CSV files
from selenium.common.exceptions import TimeoutException  # Import exception handling for timeouts
import sys  # Import sys module to access command-line arguments
import argparse  # Import argparse for command-line argument parsing
import json
import random
import time


class HeadlessBrowser:
    def __init__(self):
        # Ensure the correct chromedriver version is installed
        chromedriver_autoinstaller.install()
        # Get the major version of Chrome
        chrome_version = int(chromedriver_autoinstaller.get_chrome_version().split('.')[0])
        print(f"Installed Chrome version: {chrome_version}")

        # Initialize the Chrome driver with specified options and version
        self.driver = uc.Chrome(
            options=self.get_options(),
            version_main=chrome_version  # Use the detected Chrome version here
        )

    def get_options(self):
        # Set Chrome options for the headless browser
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')  # Bypass OS security model
        options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
        options.add_argument('--disable-blink-features=AutomationControlled')  # Disable automation controls
        return options

    def quit(self):
        # Close the browser and end the session
        self.driver.quit()


class Browser:
    number_of_windows = 0  # Class variable to track the number of open windows
    current_window = 0  # Class variable to track the current window index

    def __init__(self):
        # Initialize the browser with a headless browser instance
        self.headless_browser = HeadlessBrowser()
        self.variables = {}  # Dictionary to store variables and scraped data
        self.instruction_pointer = 0  # Pointer to keep track of instruction index
        self.instructions = []  # List to store instructions
        self.loop_stack = []  # Stack to handle nested loops
        
        # Load environment variables
        self.linkedin_email = os.getenv('LINKEDIN_EMAIL')
        self.linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        
        if not self.linkedin_email or not self.linkedin_password:
            # Try loading from .env file if environment variables are not set
            try:
                from dotenv import load_dotenv
                load_dotenv()
                self.linkedin_email = os.getenv('LINKEDIN_EMAIL')
                self.linkedin_password = os.getenv('LINKEDIN_PASSWORD')
            except ImportError:
                logging.warning("python-dotenv not installed. Using environment variables only.")

    def navigate(self, url):
        # Navigate to the specified URL
        self.headless_browser.driver.get(url)

    """
    # Methods for managing browser windows (currently commented out)
    def switch_to_previous_window(self):
        self.headless_browser.driver.switch_to.window(self.headless_browser.driver.window_handles[self.current_window-1])
    def new_window(self):
        self.headless_browser.driver.execute_script("window.open('google.com');") 
        self.number_of_windows += 1
        sleep(100)
        self.headless_browser.driver.switch_to.window(self.headless_browser.driver.window_handles[self.number_of_windows])
        self.current_window = self.number_of_windows
        print(f"number of open  windows {self.number_of_windows}")
        return(self.number_of_windows)
    def navigate_to_window(self,window_number):
        self.headless_browser.driver.switch_to.window(self.headless_browser.driver.window_handles[window_number])
    """

    def close(self):
        # Close the browser session
        self.headless_browser.quit()

    def fill_input(self, selector, value):
        """Fill an input field identified by a CSS selector."""
        # Use the custom function to fill the input field
        fill_input(self.headless_browser.driver, selector, value)

    def click_element_by_selector(self, selector):
        """Click an element identified by a CSS selector."""
        # Use the custom function to click the element
        click_element_by_selector(self.headless_browser.driver, selector)

    def load_cookies_from_file(self, path):
        """Load cookies from a specified file into the browser."""
        # Use the custom function to load cookies
        load_cookies(self.headless_browser.driver, path)

    def save_cookies_to_file(self, output_file_path):
        """Save cookies to a file in the specified directory."""
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        # Use the custom function to save cookies
        save_cookies(self.headless_browser.driver, output_file_path)

    def get_inner_text(self, selector):
        """Get the inner text of an element identified by a CSS selector."""
        # Use the custom function to get inner text
        return get_inner_text(self.headless_browser.driver, selector)

    def get_attribute(self, selector, attribute):
        """Get the value of a specified attribute from an element identified by a CSS selector."""
        # Use the custom function to get the attribute value
        return get_attribute_value(self.headless_browser.driver, selector, attribute)

    def get_inner_text_list(self, selector):
        """Get a list of inner texts from elements identified by an XPath selector."""
        elements = find_elements_by_xpath(self.headless_browser.driver, selector)
        return [element.text for element in elements]

    def save_to_csv(self, filename):
        """Save the variables dictionary to a CSV file."""
        fieldnames = list(self.variables.keys())

        # Check if the file exists to determine whether to write headers
        file_exists = os.path.isfile(filename)

        # Open the CSV file in append mode
        with open(filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # Write header only if the file does not exist
            if not file_exists:
                writer.writeheader()

            # Write the variables to the CSV file
            writer.writerow(self.variables)

        # Clear variables after saving to prevent data overlap
        self.variables.clear()

    def is_logged_in(self):
        """Check if the user is logged into LinkedIn."""
        try:
            # Navigate to LinkedIn
            self.headless_browser.driver.get("https://www.linkedin.com/")
            time.sleep(3)  # Wait for page to load
            
            # Look for guest navigation elements
            guest_elements = self.headless_browser.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'nav__cta-container')]//a[contains(@data-tracking-control-name, 'guest_homepage')]"
            )
            
            # If no guest elements are found, user is likely logged in
            return len(guest_elements) == 0
            
        except Exception as e:
            logging.error(f"Error checking login status: {e}")
            return False

    def ensure_logged_in(self, cookies_file):
        """Ensure the browser is logged into LinkedIn."""
        try:
            # Create cookies directory if it doesn't exist
            os.makedirs(os.path.dirname(cookies_file), exist_ok=True)
            
            # First try to load cookies if they exist
            if os.path.exists(cookies_file):
                self.load_cookies_from_file(cookies_file)
                # Navigate to LinkedIn and check login status
                self.headless_browser.driver.get("https://www.linkedin.com/")
                time.sleep(3)  # Wait for page to load
                
                # Check if already logged in by looking for nav menu
                try:
                    nav_menu = WebDriverWait(self.headless_browser.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//nav[contains(@class, 'global-nav')]"))
                    )
                    logging.info("Already logged in via cookies")
                    return True
                except TimeoutException:
                    logging.info("Not logged in, proceeding with login process")
            
            # If we reach here, either cookies don't exist or didn't work
            if not self.linkedin_email or not self.linkedin_password:
                raise ValueError("LinkedIn credentials not found in environment variables or .env file")
            
            # Set variables for login instructions
            self.variables['LINKEDIN_EMAIL'] = self.linkedin_email
            self.variables['LINKEDIN_PASSWORD'] = self.linkedin_password
            self.variables['COOKIES_FILE'] = cookies_file
            
            # Execute login instructions
            login_instructions_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                                 "instructions", "login_instructions.txt")
            
            if not os.path.exists(login_instructions_file):
                raise FileNotFoundError(f"Login instructions file not found: {login_instructions_file}")
            
            self.execute_instructions(login_instructions_file)
            
            # Verify login was successful
            if not self.is_logged_in():
                raise Exception("Failed to log in to LinkedIn")
            
            # Save cookies after successful login
            logging.info("Login successful, saving cookies")
            self.save_cookies_to_file(cookies_file)
            
            logging.info("Successfully logged in to LinkedIn and saved cookies")
            return True
            
        except Exception as e:
            logging.error(f"Error ensuring login: {e}")
            return False

    def execute_instructions(self, file_path):
        """Execute instructions from a text file."""
        # Load all instructions into a list
        with open(file_path, 'r') as file:
            self.instructions = [line.strip() for line in file if line.strip() and not line.strip().startswith('#')]

        # Reset instruction pointer and loop stack
        self.instruction_pointer = 0
        self.loop_stack = []

        # Execute instructions
        while self.instruction_pointer < len(self.instructions):
            line = self.instructions[self.instruction_pointer]
            if line.startswith('FOR_EACH_URL'):
                # Store the loop start position
                self.loop_stack.append({
                    'start_pointer': self.instruction_pointer,
                    'current_url_index': 0
                })
            
            result = self.execute_command(line)
            
            # Handle loop iteration
            if line == 'END_FOR' and self.loop_stack:
                current_loop = self.loop_stack[-1]
                current_loop['current_url_index'] += 1
                if hasattr(self, 'urls') and current_loop['current_url_index'] < len(self.urls):
                    # Go back to start of loop
                    self.instruction_pointer = current_loop['start_pointer']
                else:
                    # Loop finished, remove it from stack
                    self.loop_stack.pop()
            
            self.instruction_pointer += 1

    def execute_command(self, line):
        """Parse and execute a single instruction line with variable substitution."""
        # Replace variables in the line
        line = self.replace_variables(line)
        parts = line.strip().split(' ', 1)
        command = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ''

        try:
            if command == 'FOR_EACH_URL':
                # Parse the file path from "IN ${URLS_FILE}"
                if not args.upper().startswith('IN'):
                    raise ValueError("Invalid FOR_EACH_URL syntax. Use: FOR_EACH_URL IN file_path")
                file_path = args.split(' ', 1)[1].strip()
                # Store URLs for iteration
                with open(file_path, 'r') as f:
                    self.urls = [line.strip() for line in f if line.strip()]
                if self.loop_stack:
                    self.current_url_index = self.loop_stack[-1]['current_url_index']
                return True
                
            elif command == 'VISIT_URL':
                if hasattr(self, 'urls') and self.loop_stack:
                    current_loop = self.loop_stack[-1]
                    if current_loop['current_url_index'] < len(self.urls):
                        url = self.urls[current_loop['current_url_index']]
                        self.headless_browser.driver.get(url)
                        return True
                return False
                
            elif command == 'WAIT':
                sleep(float(args.strip()))
                return True
                
            elif command == 'WAIT_RANDOM':
                min_max = args.split('-')
                wait_time = random.uniform(float(min_max[0]), float(min_max[1]))
                sleep(wait_time)
                return True
                
            elif command == 'SAVE_TO':
                # Save the current data to the specified file
                output_file = args.strip()
                if hasattr(self, 'current_data') and self.current_data:
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
                    
                    # Load existing data to check for duplicates
                    existing_profiles = []
                    if os.path.exists(output_file):
                        try:
                            with open(output_file, 'r') as f:
                                for line in f:
                                    if line.strip():
                                        try:
                                            profile = json.loads(line)
                                            existing_profiles.append(profile)
                                        except json.JSONDecodeError:
                                            continue
                        except Exception as e:
                            logging.error(f"Error reading existing profiles from {output_file}: {e}")
                    
                    # Check if profile is duplicate
                    is_duplicate = False
                    if 'linkedin_url' in self.current_data:
                        current_url = self.current_data.get('linkedin_url')
                        if current_url:  # Only check if URL is not None
                            for profile in existing_profiles:
                                if profile.get('linkedin_url') == current_url:
                                    is_duplicate = True
                                    logging.info(f"Skipping duplicate profile: {current_url}")
                                    break
                    
                    # Append new data if not duplicate
                    if not is_duplicate:
                        try:
                            with open(output_file, 'a') as f:
                                json.dump(self.current_data, f)
                                f.write('\n')
                            logging.info(f"Profile saved to {output_file}")
                        except Exception as e:
                            logging.error(f"Error saving profile to {output_file}: {e}")
                    
                    # Reset current_data after saving or skipping
                    self.current_data = {}
                return True
                
            elif command == 'END_FOR':
                return True  # Actual loop handling is done in execute_instructions
                
            elif command == 'MARK_COMPLETE':
                logging.info("Processing completed successfully")
                return True

            elif command == 'NAVIGATE':
                self.navigate(args.strip())
            elif command == 'SLEEP':
                sleep(float(args.strip()))
            elif command == 'WAIT_FOR':
                # Args format: "selector"
                selector = args.strip('"\'')
                WebDriverWait(self.headless_browser.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
            elif command == 'WAIT_CLICKABLE':
                # Args format: "selector"
                selector = args.strip('"\'')
                WebDriverWait(self.headless_browser.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
            elif command == 'CLICK_ELEMENT_BY_SELECTOR':
                selector = args.strip('"\'')
                element = self.headless_browser.driver.find_element(By.XPATH, selector)
                element.click()
            elif command == 'EXTRACT':
                # Parse the JSON rules from args
                start_idx = args.find('{')
                end_idx = args.rfind('}')
                if start_idx == -1 or end_idx == -1:
                    logging.error("Invalid EXTRACT format")
                    return None

                rules_dict = json.loads(args[start_idx:end_idx + 1])
                
                # Initialize current_data if it doesn't exist
                if not hasattr(self, 'current_data'):
                    self.current_data = {}
                
                # Extract data according to rules
                for field, xpath in rules_dict.items():
                    try:
                        if xpath.endswith('/@href'):  # Handle attribute extraction
                            # Remove /@href from xpath and get the attribute separately
                            base_xpath = xpath.replace('/@href', '')
                            elements = self.headless_browser.driver.find_elements(By.XPATH, base_xpath)
                            if elements:
                                if len(elements) == 1:
                                    self.current_data[field] = elements[0].get_attribute('href')
                                else:
                                    self.current_data[field] = [elem.get_attribute('href') for elem in elements]
                            else:
                                self.current_data[field] = None
                        else:
                            elements = self.headless_browser.driver.find_elements(By.XPATH, xpath)
                            if elements:
                                if len(elements) == 1:
                                    self.current_data[field] = elements[0].text.strip()
                                else:
                                    self.current_data[field] = [elem.text.strip() for elem in elements]
                            else:
                                self.current_data[field] = None
                    except Exception as e:
                        logging.warning(f"Error extracting {field}: {e}")
                        self.current_data[field] = None
                
                return self.current_data
            elif command == 'GET_INNER_TEXT':
                # Args format: "selector" variable_name
                selector, var_name = self.parse_args(args)
                text = self.get_inner_text(selector)
                self.variables[var_name] = text
            elif command == 'GET_ATTRIBUTE':
                # Args format: "selector" attribute_name variable_name
                selector, attribute_name, var_name = self.parse_args(args, expected_args=3)
                value = self.get_attribute(selector, attribute_name)
                self.variables[var_name] = value
            elif command == 'GET_INNER_TEXT_LIST':
                # Args format: "selector" variable_name [separator]
                parts = self.parse_args_flexible(args)
                selector, var_name = parts[0], parts[1]
                separator = parts[2] if len(parts) > 2 else ', '
                texts = self.get_inner_text_list(selector)
                self.variables[var_name] = separator.join(texts)
            elif command == 'FILL_INPUT':
                # Args format: "selector" value
                selector, value = self.parse_args(args)
                self.fill_input(selector, value)
            elif command == 'SAVE_TO_CSV':
                filename = args.strip()
                self.save_to_csv(filename)
            elif command == 'SET':
                var_name, value = args.split(' ', 1)
                self.variables[var_name.strip()] = value.strip()
            elif command == 'PRINT':
                # Print variable or text
                value = args.strip()
                if value.startswith('${') and value.endswith('}'):
                    var_name = value[2:-1]
                    print(f"{var_name}: {self.variables.get(var_name, 'Not found')}")
                else:
                    print(value)
            elif command == 'IF':
                # Args format: variable operator value
                condition = self.evaluate_condition(args)
                if not condition:
                    self.skip_until('ENDIF')
            elif command == 'ENDIF':
                pass  # Just a marker for IF blocks
            elif command == 'LOOP':
                # Support both file-based and list-based loops
                # Args format: variable_name IN filepath
                # or: variable_name IN [item1, item2, ...]
                loop_var = args.split(' ', 1)[0].strip()
                remaining = args.split(' ', 1)[1].strip()
                
                if not remaining.upper().startswith('IN'):
                    raise ValueError("Invalid LOOP syntax. Use: LOOP var_name IN source")
                
                source = remaining[2:].strip()
                
                if source.startswith('[') and source.endswith(']'):
                    # List-based loop
                    items = [item.strip() for item in source[1:-1].split(',')]
                else:
                    # File-based loop
                    with open(source.strip(), 'r') as f:
                        items = [line.strip() for line in f if line.strip()]
                
                self.loop_stack.append({
                    'loop_var': loop_var,
                    'items': items,
                    'current_index': 0,
                    'start_pointer': self.instruction_pointer
                })
                
                if items:
                    self.variables[loop_var] = items[0]
                else:
                    self.skip_loop()
            elif command == 'ENDLOOP':
                if not self.loop_stack:
                    raise ValueError("ENDLOOP found without matching LOOP")
                loop_info = self.loop_stack[-1]
                loop_info['current_index'] += 1
                if loop_info['current_index'] < len(loop_info['items']):
                    self.variables[loop_info['loop_var']] = loop_info['items'][loop_info['current_index']]
                    self.instruction_pointer = loop_info['start_pointer']
                else:
                    self.loop_stack.pop()
            elif command == 'SCROLL_TO':
                # Args format: "selector"
                selector = args.strip('"\'')
                element = self.headless_browser.driver.find_element(By.XPATH, selector)
                self.headless_browser.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            elif command == 'SCROLL':
                # Args format: direction (UP/DOWN) [pixels]
                parts = args.split()
                direction = parts[0].upper()
                pixels = int(parts[1]) if len(parts) > 1 else 300
                if direction == 'UP':
                    pixels = -pixels
                self.headless_browser.driver.execute_script(f"window.scrollBy(0, {pixels});")
            elif command == 'SAVE_TO_FILE':
                # Save cookies to file
                self.save_cookies_to_file(args.strip())
                return True
            else:
                logging.warning(f"Unknown command: {command}")
                return None

        except Exception as e:
            logging.error(f"Error executing command '{line}': {e}")
            return None

    def evaluate_condition(self, condition):
        """Evaluate a condition for IF statements."""
        parts = condition.split()
        if len(parts) != 3:
            raise ValueError("Invalid condition format. Use: variable operator value")
        
        var_name, operator, value = parts
        var_value = self.variables.get(var_name)
        
        if operator == '==':
            return str(var_value) == value
        elif operator == '!=':
            return str(var_value) != value
        elif operator == 'CONTAINS':
            return value in str(var_value)
        elif operator == 'NOT_CONTAINS':
            return value not in str(var_value)
        else:
            raise ValueError(f"Unknown operator: {operator}")

    def skip_until(self, end_command):
        """Skip instructions until the specified end command is found."""
        while self.instruction_pointer < len(self.instructions) - 1:
            self.instruction_pointer += 1
            line = self.instructions[self.instruction_pointer]
            cmd = line.strip().split(' ', 1)[0].upper()
            if cmd == end_command:
                break

    def parse_args_flexible(self, args):
        """Parse arguments from a command line with optional parameters."""
        parts = []
        current = ''
        in_quotes = False
        quote_char = ''
        
        for c in args:
            if c in ('"', "'"):
                if in_quotes and c == quote_char:
                    in_quotes = False
                elif not in_quotes:
                    in_quotes = True
                    quote_char = c
                else:
                    current += c
            elif c == ' ' and not in_quotes:
                if current:
                    parts.append(current)
                    current = ''
            else:
                current += c
                
        if current:
            parts.append(current)
            
        return parts

    def skip_loop(self):
        """Skip instructions until ENDLOOP is found."""
        nested_loops = 1
        while nested_loops > 0 and self.instruction_pointer < len(self.instructions) - 1:
            self.instruction_pointer += 1
            line = self.instructions[self.instruction_pointer]
            cmd = line.strip().split(' ', 1)[0].upper()
            if cmd == 'LOOP':
                nested_loops += 1
            elif cmd == 'ENDLOOP':
                nested_loops -= 1

    def replace_variables(self, line):
        """Substitute variables in the instruction line."""
        for var_name, value in self.variables.items():
            placeholder = f'${{{var_name}}}'
            if placeholder in line:
                line = line.replace(placeholder, value)
        return line

    def parse_args(self, args, expected_args=2):
        """Parse arguments from a command line."""
        parts = []
        current = ''
        in_quotes = False
        quote_char = ''
        for c in args:
            if c in ('"', "'"):
                if in_quotes and c == quote_char:
                    in_quotes = False
                elif not in_quotes:
                    in_quotes = True
                    quote_char = c
                else:
                    current += c  # Inside quotes, different quote character
            elif c == ' ' and not in_quotes:
                if current:
                    parts.append(current)
                    current = ''
            else:
                current += c
        if current:
            parts.append(current)

        if len(parts) != expected_args:
            raise ValueError(f"Expected {expected_args} arguments, got {len(parts)}")
        return parts

    def scrape_profiles(self, urls_file, instructions_file, output_file):
        """Execute scraping instructions for a list of URLs"""
        try:
            # Read URLs from file
            with open(urls_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]

            # Read instructions file
            with open(instructions_file, 'r') as f:
                self.instructions = f.readlines()

            results = []
            for url in urls:
                try:
                    logging.info(f"Processing URL: {url}")
                    self.headless_browser.driver.get(url)
                    
                    # Execute instructions for this URL
                    for instruction in self.instructions:
                        instruction = instruction.strip()
                        if not instruction or instruction.startswith('#'):
                            continue
                        
                        if instruction.startswith('WAIT '):
                            time.sleep(float(instruction.split()[1]))
                        elif instruction.startswith('WAIT_RANDOM '):
                            min_max = instruction.split()[1].split('-')
                            wait_time = random.uniform(float(min_max[0]), float(min_max[1]))
                            time.sleep(wait_time)
                        elif instruction.startswith('EXTRACT '):
                            data = self.execute_command(instruction)
                            if data:
                                results.append(data)
                                with open(output_file, 'w') as f:
                                    json.dump(results, f, indent=2)
                        elif instruction == 'MARK_COMPLETE':
                            logging.info("Profile scraping completed successfully")
                        
                except Exception as e:
                    logging.error(f"Error processing URL {url}: {e}")
                    continue

            return True

        except Exception as e:
            logging.error(f"Error in scrape_profiles: {e}")
            return False

# Example usage:
if __name__ == "__main__":
    def main():
        """Main function to initiate the instruction execution."""
        parser = argparse.ArgumentParser(description='Browser automation script.')
        parser.add_argument('-i', '--instructions', required=True, help='Path to the instructions file.')
        args = parser.parse_args()

        instructions_file = args.instructions

        browser = Browser()  # Create a new Browser instance
        #browser.save_cookies_to_file("cookies.txt")
        browser.load_cookies_from_file("cookies.txt")  # Load cookies for authentication (if needed)
        browser.execute_instructions(instructions_file)  # Execute instructions from the specified file
        print("Scraped Data:", browser.variables)
        browser.close()  # Close the browser session

    # Execute the main function when the script is run
    main()
