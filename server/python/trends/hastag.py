from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

# Set up Chrome options
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode
options.add_argument('--disable-gpu')  # Disable GPU acceleration
options.add_argument('--no-sandbox')  # Bypass OS security model
options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
options.add_argument('--window-size=1920,1080')  # Set window size to simulate full screen

# Initialize WebDriver
driver = webdriver.Chrome(options=options)

try:
    # Navigate to the target page
    driver.get('https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en')

    # Wait for the "View More" button to be visible
    button_xpath = '//*[@id="ccContentContainer"]/div[3]/div/div[2]/div/div[1]'
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, button_xpath))
    )

    # Find and click the button 5 times
    button = driver.find_element(By.XPATH, button_xpath)
    for i in range(5):
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        time.sleep(1)  # Wait for scrolling to complete
        driver.execute_script("arguments[0].click();", button)
        print(f"Clicked the button {i + 1} time(s)")
        time.sleep(2)  # Wait for new content to load

    # Wait for elements with the target XPath to be present
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//*[@id="hashtagItemContainer"]'))
    )

    # Extract and filter text from each element matching the XPath
    elements = driver.find_elements(By.XPATH, '//*[@id="hashtagItemContainer"]')
    for element in elements:
        text = element.text.strip()
        # Split the text into lines and filter the desired ones
        lines = text.split('\n')
        for line in lines:
            # Print only lines starting with "#" or ending with "K"
            if line.startswith('#') or re.match(r'.*\d+K$', line):
                print(line)

finally:
    # Quit the WebDriver
    driver.quit()
