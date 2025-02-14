from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
def get_attribute_value(driver, selector, attribute):
    """Get the value of a specified attribute from an element identified by a CSS selector."""
    # Wait for the element to be visible
    try:
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, selector)))
        return element.get_attribute(attribute)
    except TimeoutException:
        print(f"error with selector {selector}")
