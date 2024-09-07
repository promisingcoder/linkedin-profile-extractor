from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException

def click_element_by_selector(driver, selector):
    """Click an element identified by a CSS selector."""
    try:
        # Wait for the element to be present and clickable
        element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, selector)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        clickable_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, selector)))
        clickable_element.click()  # Click the element

    except (TimeoutException, ElementClickInterceptedException) as e:
        print(f"Warning: Element with selector '{selector}' not found or not clickable. Error: {e}")
        # Optionally, attempt JavaScript click as a fallback
        try:
            driver.execute_script("arguments[0].click();", element)
        except Exception as js_error:
            print(f"JavaScript click also failed: {js_error}")
        # Log a screenshot for further debugging if needed
        driver.save_screenshot("screenshot.png")
