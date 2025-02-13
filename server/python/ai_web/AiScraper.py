from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import json
import re
import datetime
from concurrent.futures import ThreadPoolExecutor
import sys

def set_up_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)
    return driver

# Function to scrape a single website
def scrape_website(url, category):
    driver = set_up_driver()
    driver.get(url)
    time.sleep(3)  # Allow time for the page to load

    articles = driver.find_elements(By.CSS_SELECTOR, "article")
    scraped_data = []

    for article in articles:
        try:
            title_element = article.find_element(By.CSS_SELECTOR, "h2.entry-title a")
            title = title_element.text
            link = title_element.get_attribute("href")
            scraped_data.append({"title": title, "link": link, "category": category})
        except Exception as e:
            print(f"Error scraping article from {url}: {e}")

    driver.quit()
    return scraped_data

def scrape_paragraphs(url):
    driver = set_up_driver()
    try:
        driver.get(url)
        time.sleep(3)  

        paragraphs = driver.find_elements(By.CSS_SELECTOR, "div.entry-content p")
        paragraph_texts = [p.text.strip() for p in paragraphs if p.text.strip()]
        
        return " ".join(paragraph_texts)  # Combine paragraphs into a single string
    except Exception as e:
        print(f"Error scraping paragraphs from {url}: {e}")
        return ""
    finally:
        driver.quit()

def scrape_links(csv_file):
    data = pd.read_csv(csv_file)
    detailed_data = []

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(scrape_paragraphs, row['link']): row for _, row in data.iterrows()}
        
        for future in futures:
            row = futures[future]
            paragraphs = future.result()
            if paragraphs:
                detailed_data.append({
                    "title": row['title'],
                    "link": row['link'],
                    "category": row['category'],
                    "paragraphs": paragraphs
                })
    
    return detailed_data

# Main function
if __name__ == "__main__":
    
    start_time = time.time()

    normal_websites = [
        "https://the-indie-in-former.com/",
        "https://www.thegamer.com/tag/indie-games/",
        "https://indiegamereviewer.com/",
    ]
    marketing_websites = [
        "https://acorngames.gg/blog/2024/1/11/using-social-media-as-an-indie-game-developer",
        "https://enjin.io/blog/10-social-media-marketing-tips-for-indie-game-developers",
        "https://www.conduit.gg/blog/posts/best-channels-for-marketing-an-indie-game",
    ]

    all_data = []

    with ThreadPoolExecutor() as executor:
        futures = []
        
        # Scraping normal websites
        for website in normal_websites:
            futures.append(executor.submit(scrape_website, website, "normal"))

        # Scraping marketing websites
        for website in marketing_websites:
            futures.append(executor.submit(scrape_website, website, "marketing"))

        # Collect results
        for future in futures:
            all_data.extend(future.result())

    # Save initial scraped data
    df = pd.DataFrame(all_data, columns=["title", "link", "category"])
    csv_file = "scraped_data.csv"
    df.to_csv(csv_file, index=False)
    print(f"Initial scraping completed. Data saved to {csv_file}")

    # Scrape paragraphs for details
    detailed_data = scrape_links(csv_file)
    detailed_df = pd.DataFrame(detailed_data, columns=["title", "link", "category", "paragraphs"])
    detailed_df.to_csv("detailed_data.csv", index=False)
    print("Paragraph scraping completed. Data saved to detailed_data.csv")

    # Separate normal and marketing data into two different CSVs
    normal_df = detailed_df[detailed_df["category"] == "normal"]
    marketing_df = detailed_df[detailed_df["category"] == "marketing"]

    normal_df.to_csv("normal_websites_data.csv", index=False)
    marketing_df.to_csv("marketing_websites_data.csv", index=False)

    print("Separated normal and marketing website data into individual files.")

    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nTotal Execution Time: {datetime.timedelta(seconds=int(total_time))}")
    sys.exit()
