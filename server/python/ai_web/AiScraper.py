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

# Function to scrape data from links within the CSV
def scrape_links(csv_file):
    data = pd.read_csv(csv_file)
    detailed_data = []

    for _, row in data.iterrows():
        link = row['link']
        print(f"Scraping details for: {link}")
        driver = set_up_driver()
        try:
            driver.get(link)
            time.sleep(3)

            # Example: Extract the main content or other details
            content_element = driver.find_element(By.CSS_SELECTOR, "div.entry-content")
            content = content_element.text
            detailed_data.append({"title": row['title'], "link": link, "content": content})
        except Exception as e:
            print(f"Error scraping link: {e}")
        finally:
            driver.quit()

    return detailed_data

# Main function
if __name__ == "__main__":
    # List of websites to scrape
    websites = [
        "https://the-indie-in-former.com/",
        "https://www.thegamer.com/tag/indie-games/",
        "https://indiegamereviewer.com/",
    ]
    
    # Scrape all websites and save results to CSV
    all_data = []
    for website in websites:
        print(f"Scraping website: {website}")
        data = scrape_website(website)
        all_data.extend(data)
    
    # Save initial data to CSV
    df = pd.DataFrame(all_data, columns=["title", "link"])
    csv_file = "scraped_data.csv"
    df.to_csv(csv_file, index=False)
    print(f"Initial scraping completed. Data saved to {csv_file}")
    
    # Scrape additional details from links in the CSV
    detailed_data = scrape_links(csv_file)
    detailed_df = pd.DataFrame(detailed_data, columns=["title", "link", "content"])
    detailed_df.to_csv("detailed_data.csv", index=False)
    print("Detailed scraping completed. Data saved to detailed_data.csv")