import os
import shutil
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_logging():
    logging.basicConfig(filename='browser.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def save_linkedin_profile_as_pdf(browser, profile_url, base_directory):
    """Visit the LinkedIn profile and save it as a PDF using the Browser instance."""
    setup_logging()
    logging.info(f"Starting to save LinkedIn profile from {profile_url}")

    # Navigate to the profile URL
    browser.navigate(profile_url)
    
    try:
        # Use XPath to target the "More actions" button
        browser.click_element("//button[contains(@aria-label, 'More actions') and contains(@class, 'artdeco-dropdown__trigger')]")
        
        # Wait for the "Save to PDF" option to be visible and clickable
        WebDriverWait(browser.headless_browser.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Save to PDF']"))
        )
        browser.click_element("//span[text()='Save to PDF']")
        
        # Wait for the download to complete
        WebDriverWait(browser.headless_browser.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//h1[@class='text-heading-xlarge']"))
        )
        
        # Extract the profile name from the h1 element
        profile_name = browser.get_inner_text("//h1[@class='text-heading-xlarge']").strip()
        logging.info(f"Profile name extracted: {profile_name}")
        
        # Ensure the base directory exists
        if not os.path.exists(base_directory):
            os.makedirs(base_directory)
            logging.info(f"Created base directory: {base_directory}")

        # Define the new directory based on the profile name
        profile_directory = os.path.join(base_directory, profile_name)
        if not os.path.exists(profile_directory):
            os.makedirs(profile_directory)
            logging.info(f"Created profile directory: {profile_directory}")

        # Define the path where the PDF will be saved
        pdf_path = os.path.join(profile_directory, "Profile.pdf")

        # Define the path where the PDF is downloaded
        downloads_folder = os.path.expanduser(r"C:\Users\mgnmt\Downloads")
        pdf_downloaded_path = os.path.join(downloads_folder, "Profile.pdf")

        if os.path.exists(pdf_downloaded_path):
            shutil.move(pdf_downloaded_path, pdf_path)
            logging.info(f"Moved PDF to: {pdf_path}")
        else:
            logging.error(f"PDF file not found at: {pdf_downloaded_path}")

        return profile_name
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None
