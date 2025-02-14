from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fill_input(driver, selector, value):
    """Fill an input field identified by a CSS selector."""
    # Wait for the element to be visible
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, selector)))
    input_field = driver.find_element(By.CSS_SELECTOR, selector)
    input_field.clear()  # Clear existing text
    input_field.send_keys(value)