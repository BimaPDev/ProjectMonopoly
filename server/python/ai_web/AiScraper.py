from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
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
    options.add_argument("--enable-unsafe-swiftshader")
    driver = webdriver.Chrome(options=options)
    return driver

# Function to scrape a single website
def scrape_website(url):
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
            scraped_data.append({"title": title, "link": link})
        except Exception as e:
            print(f"Error scraping article: {e}")

    driver.quit()
    return scraped_data

def clean_text(text):
    # List of common sharing/social media text patterns to remove
    share_texts = [
        "Click to share on Facebook",
        "Click to share on Reddit", 
        "Click to share on LinkedIn",
        "Click to share on WhatsApp",
        "Click to share on Threads",
        "Click to share on Bluesky",
        "Click to share on Mastodon", 
        "Click to share on Telegram",
        "Click to share on Pinterest",
        "Click to share on X",
        "Click to print",
        "Click to email a link to a friend"
    ]
    
    
    for share_text in share_texts:
        text = text.replace(share_text, "")
    
    
    text = re.sub(r'http\S+', '', text)
    
    
    text = ' '.join(text.split())
    
    return text

def scrape_paragraphs(url):
    driver = set_up_driver()
    try:
        driver.get(url)
        time.sleep(3)  

        
        paragraphs = driver.find_elements(By.CSS_SELECTOR, "div.entry-content p")
        
        
        paragraph_texts = [
            clean_text(p.text.strip()) 
            for p in paragraphs 
            if p.text.strip()  
        ]
        
        return paragraph_texts
    except Exception as e:
        print(f"Error scraping paragraphs from {url}: {e}")
        return []
    finally:
        driver.quit()

def scrape_links(csv_file):
    data = pd.read_csv(csv_file)
    detailed_data = []

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(scrape_paragraphs, row['link'])  # Still pass the 'link' for scraping paragraphs
            for _, row in data.iterrows()
        ]
        
        for future, row in zip(futures, data.iterrows()):
            paragraphs = future.result()

            if paragraphs:
                detailed_data.append({
                    "title": row[1]['title'],  # Save only the title and paragraphs
                    "paragraphs": " ".join(paragraphs)
                })

    return detailed_data

# Main function
if __name__ == "__main__":
    
    start_time = time.time()

    websites = [
        "https://the-indie-in-former.com/",
        "https://www.thegamer.com/tag/indie-games/",
        "https://indiegamereviewer.com/",
    ]

    
    all_data = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(scrape_website, website) for website in websites]
        
        for future in futures:
            all_data.extend(future.result())

    
    df = pd.DataFrame(all_data, columns=["title", "link"])
    csv_file = "scraped_data.csv"
    df.to_csv(csv_file, index=False)
    print(f"Initial scraping completed. Data saved to {csv_file}")

    
    detailed_data = scrape_links(csv_file)
    detailed_df = pd.DataFrame(detailed_data, columns=["title", "link", "paragraphs"])
    detailed_df.to_csv("detailed_data.csv", index=False)
    print("Paragraph scraping completed. Data saved to detailed_data.csv")

    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nTotal Execution Time: {datetime.timedelta(seconds=int(total_time))}")
    sys.exit()