"""
TikTok Hashtag Trends Scraper
Scrapes trending hashtags from TikTok Creative Center.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import re
import logging

logger = logging.getLogger(__name__)


def scrape_hashtags(max_clicks: int = 5) -> list:
    """
    Scrape trending hashtags from TikTok Creative Center.
    
    Args:
        max_clicks: Number of times to click "View More" button
        
    Returns:
        List of hashtag dictionaries with hashtag name and engagement count
    """
    hashtags = []
    
    # Set up Chrome options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        logger.info("Navigating to TikTok Creative Center...")
        
        # Navigate to the target page
        driver.get('https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en')

        # Wait for the "View More" button to be visible
        button_xpath = '//*[@id="ccContentContainer"]/div[3]/div/div[2]/div/div[1]'
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, button_xpath))
        )

        # Find and click the button multiple times
        button = driver.find_element(By.XPATH, button_xpath)
        for i in range(max_clicks):
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", button)
            logger.debug(f"Clicked 'View More' button {i + 1} time(s)")
            time.sleep(2)

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
            current_hashtag = None
            current_engagement = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Lines starting with "#" are hashtags
                if line.startswith('#'):
                    # Save previous hashtag if exists
                    if current_hashtag and current_engagement:
                        hashtags.append({
                            'hashtag': current_hashtag,
                            'engagement': current_engagement
                        })
                    current_hashtag = line
                    current_engagement = None
                # Lines ending with "K" or containing numbers are engagement counts
                elif re.match(r'.*\d+K?$', line) or re.search(r'\d+', line):
                    # Extract engagement number
                    match = re.search(r'([\d,]+\.?\d*)\s*(K|M)?', line, re.IGNORECASE)
                    if match:
                        num_str = match.group(1).replace(',', '')
                        multiplier = match.group(2)
                        num = float(num_str)
                        if multiplier:
                            multiplier = multiplier.upper()
                            if multiplier == 'K':
                                num *= 1000
                            elif multiplier == 'M':
                                num *= 1000000
                        current_engagement = int(num)
            
            # Save last hashtag
            if current_hashtag and current_engagement:
                hashtags.append({
                    'hashtag': current_hashtag,
                    'engagement': current_engagement
                })

        logger.info(f"Scraped {len(hashtags)} trending hashtags")
        return hashtags

    except Exception as e:
        logger.error(f"Error scraping hashtags: {e}")
        return []
        
    finally:
        if driver:
            driver.quit()


def main():
    """Main function for standalone execution."""
    logging.basicConfig(level=logging.INFO)
    hashtags = scrape_hashtags()
    
    for tag in hashtags:
        print(f"{tag['hashtag']}: {tag['engagement']:,}")
    
    return hashtags


if __name__ == "__main__":
    main()
