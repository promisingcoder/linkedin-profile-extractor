import undetected_chromedriver as uc
from time import sleep
import chromedriver_autoinstaller
from click_element import click_element
from fill_input import fill_input
from load_cookies import load_cookies
from save_cookies import save_cookies
from get_attribute_value import get_attribute_value
from get_inner_text import get_inner_text
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import logging
import os
import shutil
import csv
from selenium.common.exceptions import TimeoutException



class HeadlessBrowser:
    def __init__(self):
        chromedriver_autoinstaller.install()  # Automatically installs the correct ChromeDriver
        self.driver = uc.Chrome(options=self.get_options(), version_main=127)  # Use your current Chrome major version

    def get_options(self):
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        return options

    def quit(self):
        self.driver.quit()


class Browser:
    def __init__(self):
        self.headless_browser = HeadlessBrowser()

    def navigate(self, url):
        self.headless_browser.driver.get(url)

    def close(self):
        self.headless_browser.quit()

    def fill_input(self, selector, value):
        """Fill an input field identified by a CSS selector."""
        fill_input(self.headless_browser.driver, selector, value)  # Call the existing function

    def click_element(self, selector):
        """Click an element identified by a CSS selector."""
        click_element(self.headless_browser.driver, selector)  # Call the existing function

    def load_cookies_from_file(self, path):
        """Load cookies from a specified file into the browser."""
        load_cookies(self.headless_browser.driver, path)

    def save_cookies_to_file(self, output_file_path):
        """Save cookies from the browser to a specified file."""
        save_cookies(self.headless_browser.driver, output_file_path)  # Pass the driver object

    def get_inner_text(self, selector):
        """Get the inner text of an element identified by a CSS selector."""
        return get_inner_text(self.headless_browser.driver, selector)

    def get_attribute(self, selector, attribute):
        """Get the value of a specified attribute from an element identified by a CSS selector."""
        return get_attribute_value(self.headless_browser.driver, selector, attribute)



def scrape_profile(browser, profile_url):
    """Scrape the relevant parts of the LinkedIn profile using the Browser instance."""
    browser.navigate(profile_url)
    sleep(3)  # Wait for the page to load

    profile_data = {}
    
    try:
        # Scrape the profile name
        profile_data['name'] = browser.get_inner_text('//h1[contains(@class, "text-heading-xlarge")]')
    except TimeoutException:
        profile_data['name'] = "N/A"
        print("Profile name not found")

    try:
        # Scrape the profile headline
        profile_data['headline'] = browser.get_inner_text('//div[contains(@class, "text-body-medium break-words")]')
    except TimeoutException:
        profile_data['headline'] = "N/A"
        print("Profile headline not found")

    try:
        # Scrape the current company
        profile_data['current_company'] = browser.get_inner_text('//li[contains(@class, "pv-top-card--experience-list-item")]//span[contains(@class, "visually-hidden")]')
    except TimeoutException:
        profile_data['current_company'] = "N/A"
        print("Current company not found")

    try:
        # Scrape the location
        profile_data['location'] = browser.get_inner_text('//span[contains(@class, "text-body-small inline t-black--light break-words")]')
    except TimeoutException:
        profile_data['location'] = "N/A"
        print("Location not found")
    
    return profile_data

def scrape_contact_info(browser):
    """Click on the 'Contact info' link and scrape the contact information using the Browser instance."""
    browser.click_element('//a[@id="top-card-text-details-contact-info"]')
    sleep(2)  # Wait for the modal to load

    contact_info = {}
    
    try:
        # Scrape the LinkedIn profile URL
        contact_info['linkedin_url'] = browser.get_inner_text('//section[contains(@class, "pv-contact-info__contact-type")]//a[contains(@href, "linkedin.com/in")]')
    except TimeoutException:
        contact_info['linkedin_url'] = "N/A"
        print("LinkedIn URL not found")

    try:
        # Scrape the websites
        websites = browser.headless_browser.driver.find_elements(By.XPATH, '//section[contains(@class, "pv-contact-info__contact-type")]//a[contains(@href, "http")]')
        contact_info['websites'] = [website.get_attribute('href') for website in websites]
    except TimeoutException:
        contact_info['websites'] = []
        print("Websites not found")
    
    return contact_info

def save_to_csv(profile_data, contact_info, filename="profiles_spa.csv"):
    """Save the profile and contact information to a CSV file, appending each profile as a new row."""
    fieldnames = ['name', 'headline', 'current_company', 'location', 'linkedin_url', 'websites']
    
    # Combine profile_data and contact_info into a single dictionary
    combined_data = {**profile_data, **contact_info}
    
    # Convert websites list to a string
    combined_data['websites'] = ', '.join(combined_data['websites'])
    
    # Check if the file exists to write the header only once
    file_exists = os.path.isfile(filename)
    
    # Write to CSV
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Write header only if the file does not exist
        if not file_exists:
            writer.writeheader()
        
        # Write data
        writer.writerow(combined_data)
def get_linkedin_profiles(file_path):
    """Return a list of LinkedIn profile URLs from the given file, excluding web.archive links."""
    linkedin_profiles = []
    with open(file_path, 'r') as file:
        for line in file:
            url = line.strip()
            if "linkedin.com/in" in url and "web.archive.org" not in url:
                linkedin_profiles.append(url)
    return linkedin_profiles
def scrape_linkedin_profile(profile_url):
    browser = Browser()
    
    # Load cookies
    browser.load_cookies_from_file("cookies.txt")
    
    # Scrape profile information
    profile_data = scrape_profile(browser, profile_url)
    print("Profile Data:", profile_data)
    
    # Scrape contact information
    contact_info = scrape_contact_info(browser)
    print("Contact Info:", contact_info)
    # Save to CSV
    save_to_csv(profile_data, contact_info)
    browser.close()

def main():
    linkedin_profiles = get_linkedin_profiles('links2.txt')
    for profile_url in linkedin_profiles:
        scrape_linkedin_profile(profile_url)
        sleep(60)
main()
