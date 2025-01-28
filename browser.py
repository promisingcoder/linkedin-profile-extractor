import undetected_chromedriver as uc  # Import the undetected_chromedriver module to evade detection
from time import sleep  # Import sleep function to add delays
import chromedriver_autoinstaller  # Import to ensure the correct chromedriver version is installed
from click_element_by_selector import click_element_by_selector  # Import custom function to click elements
from fill_input import fill_input  # Import custom function to fill input fields
from load_cookies import load_cookies  # Import custom function to load browser cookies
from save_cookies import save_cookies  # Import custom function to save browser cookies
from get_attribute_value import get_attribute_value  # Import custom function to get attribute values
from get_inner_text import get_inner_text  # Import custom function to get inner text of elements
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
        """Save cookies from the browser to a specified file."""
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
        elements = self.headless_browser.driver.find_elements(By.XPATH, selector)
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
            self.execute_command(line)
            self.instruction_pointer += 1

    def execute_command(self, line):
        """Parse and execute a single instruction line with variable substitution."""
        # Replace variables in the line
        line = self.replace_variables(line)
        parts = line.strip().split(' ', 1)
        command = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ''

        try:
            if command == 'NAVIGATE':
                self.navigate(args.strip())
            elif command == 'SLEEP':
                sleep(float(args.strip()))
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
                # Args format: "selector" variable_name
                selector, var_name = self.parse_args(args)
                texts = self.get_inner_text_list(selector)
                self.variables[var_name] = ', '.join(texts)  # Join texts into a single string
            elif command == 'CLICK_ELEMENT_BY_SELECTOR':
                selector = args.strip('"\'')
                self.click_element_by_selector(selector)
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
            elif command == 'LOOP':
                # Args format: variable_name IN filepath
                loop_var, in_keyword, filepath = args.strip().split(' ', 2)
                if in_keyword.upper() != 'IN':
                    raise ValueError("Invalid LOOP syntax. Use: LOOP var_name IN filepath")
                # Read lines from the file and store in loop stack
                with open(filepath.strip(), 'r') as f:
                    items = [line.strip() for line in f if line.strip()]
                self.loop_stack.append({
                    'loop_var': loop_var.strip(),
                    'items': items,
                    'current_index': 0,
                    'start_pointer': self.instruction_pointer
                })
                # Set the first value of the loop variable
                if items:
                    self.variables[loop_var.strip()] = items[0]
                else:
                    # Skip the loop if no items
                    self.skip_loop()
            elif command == 'ENDLOOP':
                if not self.loop_stack:
                    raise ValueError("ENDLOOP found without matching LOOP")
                loop_info = self.loop_stack[-1]
                loop_info['current_index'] += 1
                if loop_info['current_index'] < len(loop_info['items']):
                    # Update loop variable and jump back to loop start
                    self.variables[loop_info['loop_var']] = loop_info['items'][loop_info['current_index']]
                    self.instruction_pointer = loop_info['start_pointer']
                else:
                    # Exit the loop
                    self.loop_stack.pop()
            else:
                print(f"Unknown command: {command}")
        except Exception as e:
            print(f"Error executing command '{line}': {e}")

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

# Example usage:
if __name__ == "__main__":
    def main():
        """Main function to initiate the instruction execution."""
        parser = argparse.ArgumentParser(description='Browser automation script.')
        parser.add_argument('-i', '--instructions', required=True, help='Path to the instructions file.')
        args = parser.parse_args()

        instructions_file = args.instructions

        browser = Browser()  # Create a new Browser instance
        browser.load_cookies_from_file("cookies.txt")  # Load cookies for authentication (if needed)
        browser.execute_instructions(instructions_file)  # Execute instructions from the specified file
        print("Scraped Data:", browser.variables)
        browser.close()  # Close the browser session

    # Execute the main function when the script is run
    main()
