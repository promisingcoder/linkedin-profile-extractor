from selenium.webdriver.common.by import By
def find_elements_by_xpath(driver,selector):
    elements  = driver.find_elements(By.XPATH,selector)
    return elements

