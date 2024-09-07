import undetected_chromedriver as uc
from time import sleep
import chromedriver_autoinstaller
from click_element_by_selector import click_element_by_selector
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
from find_elements_by_xpath import find_elements_by_xpath


class HeadlessBrowser:
    def __init__(self):

        self.driver = uc.Chrome(options=self.get_options())  # Use your current Chrome major version

    def get_options(self):
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        return options

    def quit(self):
        self.driver.quit()


class Browser:
    number_of_windows = 0
    current_window = 0
    def __init__(self):
        self.headless_browser = HeadlessBrowser()

    def navigate(self, url):
        self.headless_browser.driver.get(url)
    """
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
    def find_elements_by_xpath(self, selector):
        return(find_elements_by_xpath(self.headless_browser.driver,selector))
    def close(self):
        self.headless_browser.quit()

    def fill_input(self, selector, value):
        """Fill an input field identified by a CSS selector."""
        fill_input(self.headless_browser.driver, selector, value)  # Call the existing function

    def click_element_by_selector(self, selector):
        """Click an element identified by a CSS selector."""
        click_element_by_selector(self.headless_browser.driver, selector)  # Call the existing function

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
def scrape_linkedin_profile(browser,profile_url):

    # Load cookies
    
    
    # Scrape profile information
    profile_data = scrape_profile(browser, profile_url)
    print("Profile Data:", profile_data)
    
    # Scrape contact information
    contact_info = scrape_contact_info(browser)
    print("Contact Info:", contact_info)
    # Save to CSV
    #save_to_csv(profile_data, contact_info)
    return((profile_data,contact_info))
def extract_company_profile(browser,link):
    if link:
        browser.navigate(link)
    about_page_selector =  "//nav[contains(@class, 'org-page-navigation')]//li/a[contains(@href, '/about/') and contains(@class, 'org-page-navigation__item-anchor')]"
    overview_selector = "//section[contains(@class, 'org-page-details-module__card-spacing')]//p[contains(@class, 'text-body-medium')]"
    website_selector = "//section[contains(@class, 'org-page-details-module__card-spacing')]//h3[text()='Website']/following::dd[1]//a[@href]"
    phone_selector = "//section[contains(@class, 'org-page-details-module__card-spacing')]//h3[text()='Phone']/following::dd[1]//a[@href]"
    industry_selector = "//section[contains(@class, 'org-page-details-module__card-spacing')]//h3[text()='Industry']/following::dd[1]"
    company_size_selector = "//section[contains(@class, 'org-page-details-module__card-spacing')]//h3[text()='Company size']/following::dd[1]"
    associated_members_selector = "//section[contains(@class, 'org-page-details-module__card-spacing')]//h3[text()='Company size']/following::dd[2]//a"
    headquarters_selector = "//section[contains(@class, 'org-page-details-module__card-spacing')]//h3[text()='Headquarters']/following::dd[1]"
    founded_selector = "//section[contains(@class, 'org-page-details-module__card-spacing')]//h3[text()='Founded']/following::dd[1]"
    browser.click_element_by_selector(about_page_selector)
    overview = browser.get_inner_text(overview_selector)
    website = browser.get_attribute(website_selector,"href")
    phone = browser.get_inner_text(phone_selector)
    industry = browser.get_inner_text(industry_selector)
    company_size  = browser.get_inner_text(company_size_selector)
    associated_members = browser.get_inner_text(associated_members_selector)
    headquarters = browser.get_inner_text(headquarters_selector)
    founded= browser.get_inner_text(founded_selector)
    return({
        "overview" : overview,
        "website" : website,
        "phone" : phone,
        "industry" : industry,
        "company_size" : company_size,
        "associated_members" : associated_members,
        "headquarters" : headquarters,
        "founded" : founded
    })
def extract_job(browser,job):
    company_description_selector = "//div[@id='job-details']//strong[contains(text(),'Company Description')]/following::span/p"
    role_description_selector = "//div[@id='job-details']//strong[contains(text(),'Role Description')]/following::span/p"
    qualifications_selector = "//div[@id='job-details']//strong[contains(text(),'Qualifications')]/following::span/ul"
    company_link_selector = "//div[contains(@class, 'artdeco-entity-lockup__title')]//a[contains(@href, '/company/')]"
    profile_link_selector = "//div[contains(@class, 'hirer-card__hirer-information')]//a[contains(@class, 'app-aware-link') and contains(@href, 'linkedin.com/in/')]"

    job.click()
    sleep(2)
    company_description =  browser.get_inner_text(company_description_selector)
    role_description = browser.get_inner_text(role_description_selector)
    qualifications = browser.get_inner_text(qualifications_selector)
    company_link = browser.get_attribute(company_link_selector,"href")
    profile_link = browser.get_attribute(profile_link_selector,"href")
    sleep(10)
    #browser2 = Browser()
    #browser2.load_cookies_from_file("cookies.txt")
    """
    if profile_link:
        profile_data = scrape_linkedin_profile(browser2,profile_link)
    """
    info = {
        'company_description' : company_description,
        'role_description' : role_description,
        'qualifications' : qualifications,
        'company_link' : company_link,



    }
    """
    if profile_link:
        [info.update(item) for item in profile_data]
    info.update(extract_company_profile(browser2,company_link))
    """
    with open('jobs.csv','w') as f:
        w = csv.writer(f)
        w.writerows(info.items())
    return(info)
    
def search_for_jobs(browser,keywords,current_job_id,refresh):

    
 
    browser.navigate(f"https://www.linkedin.com/jobs/search/?currentJobId={current_job_id}&keywords={keywords}&refresh={refresh}")

    jobs = browser.find_elements_by_xpath("//li[contains(@class,'jobs-search-results__list-item')]")
    for job in jobs:
        extract_job(browser,job)

def main():
    browser = Browser()
    browser.load_cookies_from_file("cookies.txt")
    search_for_jobs(browser,"marketing","3500425629","true")

main()
