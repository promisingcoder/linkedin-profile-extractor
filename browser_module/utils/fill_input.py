from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import logging
import time

def fill_input(driver, selector, value):
    """Fill an input field identified by an XPath selector."""
    try:
        # Wait for the element with increased timeout
        wait = WebDriverWait(driver, 20)
        logging.info(f"Attempting to fill input field with selector: {selector}")
        
        # Wait for element presence and visibility
        element = wait.until(
            EC.presence_of_element_located((By.XPATH, selector))
        )
        wait.until(
            EC.visibility_of_element_located((By.XPATH, selector))
        )
        
        # Scroll element into view and ensure it's in the viewport
        driver.execute_script("""
            arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});
            const rect = arguments[0].getBoundingClientRect();
            const isInViewport = (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= window.innerHeight &&
                rect.right <= window.innerWidth
            );
            if (!isInViewport) {
                window.scrollBy(0, -100);
            }
        """, element)
        time.sleep(2)
        
        # Focus the element using JavaScript
        driver.execute_script("arguments[0].focus();", element)
        time.sleep(1)
        
        # Clear the input using multiple methods
        try:
            element.clear()
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.DELETE)
            driver.execute_script("arguments[0].value = '';", element)
        except:
            logging.warning("Standard clear failed, trying JavaScript clear")
            driver.execute_script("arguments[0].value = '';", element)
        time.sleep(1)
        
        # Type the value using JavaScript first
        driver.execute_script("""
            let element = arguments[0];
            let value = arguments[1];
            
            // Set the value
            element.value = value;
            
            // Create and dispatch input events
            element.dispatchEvent(new Event('focus', { bubbles: true }));
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
            element.dispatchEvent(new Event('blur', { bubbles: true }));
        """, element, value)
        time.sleep(1)
        
        # Verify the value was set
        actual_value = element.get_attribute('value')
        if actual_value != value:
            logging.warning(f"JavaScript input failed, trying Selenium input")
            
            # Clear again
            element.clear()
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.DELETE)
            time.sleep(1)
            
            # Type using Selenium with delays
            for char in value:
                element.send_keys(char)
                time.sleep(0.1)
            time.sleep(1)
            
            # Final verification
            actual_value = element.get_attribute('value')
            if actual_value != value:
                logging.error(f"Failed to set input value. Expected: {value}, Got: {actual_value}")
                return False
        
        logging.info(f"Successfully filled input field with value: {value}")
        return True
        
    except Exception as e:
        logging.error(f"Error filling input field: {str(e)}")
        try:
            # One last attempt using pure JavaScript
            driver.execute_script("""
                let element = arguments[0];
                let value = arguments[1];
                
                // Focus and clear
                element.focus();
                element.value = '';
                
                // Set value and trigger events
                element.value = value;
                element.dispatchEvent(new Event('focus', { bubbles: true }));
                element.dispatchEvent(new Event('input', { bubbles: true }));
                element.dispatchEvent(new Event('change', { bubbles: true }));
                element.dispatchEvent(new Event('blur', { bubbles: true }));
            """, element, value)
            time.sleep(1)
            
            if element.get_attribute('value') == value:
                logging.info("Successfully filled input using fallback JavaScript method")
                return True
        except:
            pass
        return False

def type_with_js(driver, element, value):
    """Type using JavaScript."""
    driver.execute_script("""
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
    """, element, value)
    return element.get_attribute('value') == value

def type_with_selenium(element, value):
    """Type using standard Selenium send_keys."""
    for char in value:
        element.send_keys(char)
        time.sleep(0.1)
    return element.get_attribute('value') == value

def type_with_actions(driver, element, value):
    """Type using Action Chains."""
    actions = ActionChains(driver)
    actions.click(element)
    for char in value:
        actions.send_keys(char)
        time.sleep(0.1)
    actions.perform()
    return element.get_attribute('value') == value

def standard_input(driver, element, value):
    """Standard selenium input method."""
    logging.debug("Attempting standard input method")
    element.click()
    time.sleep(0.5)
    # Try multiple clear methods
    element.clear()
    element.send_keys(Keys.CONTROL + "a")
    element.send_keys(Keys.DELETE)
    time.sleep(0.5)
    # Send keys with delay
    for char in value:
        element.send_keys(char)
        time.sleep(0.1)
    return element.get_attribute('value') == value

def js_input(driver, element, value):
    """JavaScript input method."""
    logging.debug("Attempting JavaScript input method")
    # Clear using JavaScript
    driver.execute_script("arguments[0].value = '';", element)
    # Set value and trigger events
    driver.execute_script(f"arguments[0].value = arguments[1];", element, value)
    driver.execute_script("""
        var element = arguments[0];
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        element.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true }));
        element.dispatchEvent(new KeyboardEvent('keypress', { bubbles: true }));
        element.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
    """, element)
    return element.get_attribute('value') == value

def action_chains_input(driver, element, value):
    """Action chains input method."""
    logging.debug("Attempting action chains input method")
    actions = ActionChains(driver)
    # Move to element and click
    actions.move_to_element(element).click().perform()
    time.sleep(0.5)
    
    # Clear existing value
    if element.get_attribute('value'):
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
        time.sleep(0.5)
    
    # Type value with action chains
    actions = ActionChains(driver)
    actions.click(element)
    for char in value:
        actions.send_keys(char)
        time.sleep(0.1)
    actions.perform()
    
    return element.get_attribute('value') == value