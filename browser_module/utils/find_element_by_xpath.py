from selenium.webdriver.common.by import By

def find_element_by_xpath(driver, selector):
    """Find a single element by XPath selector."""
    element = driver.find_element(By.XPATH, selector)
    return element

def find_elements_by_xpath(driver, selector):
    """Find multiple elements by XPath selector."""
    elements = driver.find_elements(By.XPATH, selector)
    return elements

