from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd

def set_up_driver():
    options = Options()
    options.add_argument("--headless")  
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    return driver

# Scrape data from the homepage
def scrape_homepage():
    driver = set_up_driver()
    url = "https://the-indie-in-former.com/"
    driver.get(url)

    time.sleep(3)  # Wait for the page to load
    
    # Locate articles on the page
    articles = driver.find_elements(By.CSS_SELECTOR, "article")
    scraped_data = []

    for article in articles:
        try:
            title_element = article.find_element(By.CSS_SELECTOR, "h2.entry-title a")
            title = title_element.text
            link = title_element.get_attribute("href")
            scraped_data.append({"title": title, "link": link})
        except Exception as e:
            print(f"Error scraping article: {e}")

    # Close the browser
    driver.quit()

    return scraped_data

# Main function
if __name__ == "__main__":
    data = scrape_homepage()

    # Convert data to a DataFrame and save to CSV
    df = pd.DataFrame(data, columns=["title", "link"])
    df.to_csv("scraped_data.csv", index=False)
