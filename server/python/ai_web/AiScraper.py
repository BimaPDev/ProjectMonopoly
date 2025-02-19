# # from selenium import webdriver
# # from selenium.webdriver.common.by import By
# # from selenium.webdriver.chrome.service import Service
# # from selenium.webdriver.chrome.options import Options
# # import time
# # import pandas as pd
# # import json
# # import re
# # import datetime
# # from concurrent.futures import ThreadPoolExecutor
# # import sys

# # def set_up_driver():
# #     options = Options()
# #     options.add_argument("--headless")
# #     options.add_argument("--disable-gpu")
# #     options.add_argument("--no-sandbox")
# #     options.add_argument("--log-level=3")
# #     options.add_argument("--enable-unsafe-swiftshader")
# #     driver = webdriver.Chrome(options=options)
# #     return driver

# # # Function to scrape a single website
# # def scrape_website(url):
# #     driver = set_up_driver()
# #     driver.get(url)
# #     time.sleep(3)  # Allow time for the page to load

# #     articles = driver.find_elements(By.CSS_SELECTOR, "article")
# #     scraped_data = []

# #     for article in articles:
# #         try:
# #             title_element = article.find_element(By.CSS_SELECTOR, "h2.entry-title a")
# #             title = title_element.text
# #             link = title_element.get_attribute("href")
# #             scraped_data.append({"title": title, "link": link})
# #         except Exception as e:
# #             print(f"Error scraping article: {e}")

# #     driver.quit()
# #     return scraped_data

# # def clean_text(text):
# #     # List of common sharing/social media text patterns to remove
# #     share_texts = [
# #         "Click to share on Facebook",
# #         "Click to share on Reddit", 
# #         "Click to share on LinkedIn",
# #         "Click to share on WhatsApp",
# #         "Click to share on Threads",
# #         "Click to share on Bluesky",
# #         "Click to share on Mastodon", 
# #         "Click to share on Telegram",
# #         "Click to share on Pinterest",
# #         "Click to share on X",
# #         "Click to print",
# #         "Click to email a link to a friend"
# #     ]
    
    
# #     for share_text in share_texts:
# #         text = text.replace(share_text, "")
    
    
# #     text = re.sub(r'http\S+', '', text)
    
    
# #     text = ' '.join(text.split())
    
# #     return text

# # def scrape_paragraphs(url):
# #     driver = set_up_driver()
# #     try:
# #         driver.get(url)
# #         time.sleep(3)  

        
# #         paragraphs = driver.find_elements(By.CSS_SELECTOR, "div.entry-content p")
        
        
# #         paragraph_texts = [
# #             clean_text(p.text.strip()) 
# #             for p in paragraphs 
# #             if p.text.strip()  
# #         ]
        
# #         return paragraph_texts
# #     except Exception as e:
# #         print(f"Error scraping paragraphs from {url}: {e}")
# #         return []
# #     finally:
# #         driver.quit()

# # def scrape_links(csv_file):
# #     data = pd.read_csv(csv_file)
# #     detailed_data = []

# #     with ThreadPoolExecutor() as executor:
# #         futures = [
# #             executor.submit(scrape_paragraphs, row['link'])  # Still pass the 'link' for scraping paragraphs
# #             for _, row in data.iterrows()
# #         ]
        
# #         for future, row in zip(futures, data.iterrows()):
# #             paragraphs = future.result()

# #             if paragraphs:
# #                 detailed_data.append({
# #                     "title": row[1]['title'],  # Save only the title and paragraphs
# #                     "paragraphs": " ".join(paragraphs)
# #                 })
    
# #     return detailed_data

# # # Main function
# # if __name__ == "__main__":
    
# #     start_time = time.time()

# #     websites = [
# #         "https://the-indie-in-former.com/",
# #         "https://www.thegamer.com/tag/indie-games/",
# #         "https://indiegamereviewer.com/",
# #     ]
# #     marketingWebsites = [
# #         "https://acorngames.gg/blog/2024/1/11/using-social-media-as-an-indie-game-developer",
# #         "https://enjin.io/blog/10-social-media-marketing-tips-for-indie-game-developers",
# #         "https://www.conduit.gg/blog/posts/best-channels-for-marketing-an-indie-game",

# #     ]
    
# #     all_data = []
# #     with ThreadPoolExecutor() as executor:
# #         futures = [executor.submit(scrape_website, website) for website in websites]
        
# #         for future in futures:
# #             all_data.extend(future.result())

    
# #     df = pd.DataFrame(all_data, columns=["title", "link"])
# #     csv_file = "scraped_data.csv"
# #     df.to_csv(csv_file, index=False)
# #     print(f"Initial scraping completed. Data saved to {csv_file}")

    
# #     detailed_data = scrape_links(csv_file)
# #     detailed_df = pd.DataFrame(detailed_data, columns=["title", "link", "paragraphs"])
# #     detailed_df.to_csv("detailed_data.csv", index=False)
# #     print("Paragraph scraping completed. Data saved to detailed_data.csv")

    
# #     end_time = time.time()
# #     total_time = end_time - start_time
# #     print(f"\nTotal Execution Time: {datetime.timedelta(seconds=int(total_time))}")
# #     sys.exit()
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# import time
# import pandas as pd
# import re
# import datetime
# from concurrent.futures import ThreadPoolExecutor
# import sys

# def set_up_driver():
#     options = Options()
#     options.add_argument("--headless")  # Remove this for debugging
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--log-level=3")
#     driver = webdriver.Chrome(options=options)
#     return driver
# def clean_text(text):
#     # List of common sharing/social media text patterns to remove
#     share_texts = [
#         "Click to share on Facebook",
#         "Click to share on Reddit", 
#         "Click to share on LinkedIn",
#         "Click to share on WhatsApp",
#         "Click to share on Threads",
#         "Click to share on Bluesky",
#         "Click to share on Mastodon", 
#         "Click to share on Telegram",
#         "Click to share on Pinterest",
#         "Click to share on X",
#         "Click to print",
#         "Click to email a link to a friend",
#         "Terms of Use",
#         "Get Started - It's Free",
#         "Cloudflare",
#     ]
    
    
#     for share_text in share_texts:
#         text = text.replace(share_text, "")
    
    
#     text = re.sub(r'http\S+', '', text)
    
    
#     text = ' '.join(text.split())
    
#     return text
# def scrape_website(url, category):
#     driver = set_up_driver()
#     driver.get(url)
#     time.sleep(3)  # Allow time for the page to load

#     print(f"Scraping {category} website: {url}")

#     scraped_data = []

#     try:
#         # Try finding articles first (common for blog content)
#         articles = driver.find_elements(By.CSS_SELECTOR, "article")
#         if not articles:
#             # If no articles found, try searching for divs that might contain articles
#             articles = driver.find_elements(By.CSS_SELECTOR, "div")
#             if not articles:
#                 # Finally, if neither articles nor divs work, try paragraphs directly
#                 paragraphs = driver.find_elements(By.CSS_SELECTOR, "p")
#                 if paragraphs:
#                     # For paragraphs, we can still extract some content
#                     for p in paragraphs:
#                         text = p.text.strip()
#                         if text:
#                             scraped_data.append({"title": text, "link": url, "category": category})
#                 else:
#                     print(f"No content found on {url}.")
#                 return scraped_data

#         # For normal websites, we can expect articles to contain titles and links
#         for article in articles:
#             try:
#                 # Try extracting the title and link from articles or divs
#                 title_element = article.find_element(By.CSS_SELECTOR, "h2.entry-title a") \
#                                     if article.find_elements(By.CSS_SELECTOR, "h2.entry-title a") else \
#                                     article.find_element(By.CSS_SELECTOR, "a")
#                 title = title_element.text
#                 link = title_element.get_attribute("href") if title_element else url  # Fallback to the page URL

#                 scraped_data.append({"title": title, "link": link, "category": category})
#             except Exception as e:
#                 print(f"Error extracting article from {url}: {e}")

#         return scraped_data

#     except Exception as e:
#         print(f"Error on {url}: {e}")
#         return []

#     finally:
#         driver.quit()

# def scrape_paragraphs(url):
#     driver = set_up_driver()
#     try:
#         driver.get(url)
#         time.sleep(3)  # Allow time for the page to load

#         # First, try to extract paragraphs (commonly used for content)
#         paragraphs = driver.find_elements(By.CSS_SELECTOR, "div.entry-content p")
#         if not paragraphs:
#             # If no paragraphs found, try extracting from divs
#             paragraphs = driver.find_elements(By.CSS_SELECTOR, "div")
#             if not paragraphs:
#                 print(f"No paragraphs or divs found on {url}.")
#                 return ""
        
#         paragraph_texts = [
#             clean_text(p.text.strip()) 
#             for p in paragraphs 
#             if p.text.strip()  
#         ]
     
#         return " ".join(paragraph_texts)  # Combine all paragraphs into one string

#     except Exception as e:
#         print(f"Error scraping paragraphs from {url}: {e}")
#         return ""
#     finally:
#         driver.quit()
# def scrape_links(csv_file):
#     data = pd.read_csv(csv_file)
#     detailed_data = []

#     with ThreadPoolExecutor() as executor:
#         futures = {executor.submit(scrape_paragraphs, row['link']): row for _, row in data.iterrows()}
        
#         for future in futures:
#             row = futures[future]
#             paragraphs = future.result()
#             if paragraphs:
#                 detailed_data.append({
#                     "title": row['title'],
#                     "link": row['link'],
#                     "category": row['category'],
#                     "paragraphs": paragraphs
#                 })
    
#     return detailed_data

# # Main function
# if __name__ == "__main__":
#     start_time = time.time()

#     normal_websites = [
#         "https://the-indie-in-former.com/",
#         "https://www.thegamer.com/tag/indie-games/",
#         "https://indiegamereviewer.com/",
#     ]
#     marketing_websites = [
#         "https://acorngames.gg/blog/2024/1/11/using-social-media-as-an-indie-game-developer",
#         "https://enjin.io/blog/10-social-media-marketing-tips-for-indie-game-developers",
#         "https://www.conduit.gg/blog/posts/best-channels-for-marketing-an-indie-game",
#     ]

#     all_data = []

#     with ThreadPoolExecutor() as executor:
#         futures = []
        
#         # Scraping normal websites
#         for website in normal_websites:
#             futures.append(executor.submit(scrape_website, website, "normal"))

#         # Scraping marketing websites
#         for website in marketing_websites:
#             futures.append(executor.submit(scrape_website, website, "marketing"))

#         # Collect results
#         for future in futures:
#             result = future.result()
#             if result:  # Only add non-empty results
#                 all_data.extend(result)

#     # Save initial scraped data
#     df = pd.DataFrame(all_data, columns=["title", "link", "category"])
#     csv_file = "scraped_data.csv"
#     df.to_csv(csv_file, index=False)
#     print(f"Initial scraping completed. Data saved to {csv_file}")

#     # Scrape paragraphs for both normal and marketing websites
#     detailed_data = scrape_links(csv_file)
#     detailed_df = pd.DataFrame(detailed_data, columns=["title", "link", "category", "paragraphs"])
#     detailed_df.to_csv("detailed_data.csv", index=False)
#     print("Paragraph scraping completed. Data saved to detailed_data.csv")

#     # Separate normal and marketing data into two different CSVs
#     normal_df = detailed_df[detailed_df["category"] == "normal"]
#     marketing_df = detailed_df[detailed_df["category"] == "marketing"]

#     normal_df.to_csv("normal_websites_data.csv", index=False)
#     marketing_df.to_csv("marketing_websites_data.csv", index=False)

#     print("Separated normal and marketing website data into individual files.")

#     end_time = time.time()
#     total_time = end_time - start_time
#     print(f"\nTotal Execution Time: {datetime.timedelta(seconds=int(total_time))}")
#     sys.exit()
from selenium import webdriver
import shutil
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
import pandas as pd
import re
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import logging
import random
from urllib.parse import urlparse
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def set_up_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")
    # Add user agent to avoid detection
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    
    # Add a proxy if needed
    # options.add_argument('--proxy-server=ip_addr:port')
    
    driver = webdriver.Chrome(options=options)
    return driver

def clean_text(text):
    if not text:
        return ""
        
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
        "Click to email a link to a friend",
        "Terms of Use",
        "Get Started - It's Free",
        "Cloudflare",
    ]
    
    for share_text in share_texts:
        text = text.replace(share_text, "")
    
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove non-breaking spaces
    text = text.replace('\xa0', ' ')
    # Remove common ads and cookie messages
    text = re.sub(r'(accept all cookies|cookie policy|privacy policy|accept cookies|we use cookies)', '', text, flags=re.IGNORECASE)
    
    return text

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def scrape_website(url, category, max_retries=2):
    retries = 0
    while retries <= max_retries:
        driver = set_up_driver()
        try:
            logger.info(f"Scraping {category} website: {url}")
            driver.get(url)
            
            # Wait for page to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for page to load: {url}")
            
            # Random pause to avoid detection
            time.sleep(random.uniform(2, 5))
            
            scraped_data = []
            
            # Define article selectors by priority
            article_selectors = [
                "article", 
                "div.post", 
                "div.entry", 
                ".blog-post", 
                ".news-item",
                ".card",
                "section.content div",
                ".article"
            ]
            
            # Try to find articles using selectors
            articles = []
            for selector in article_selectors:
                articles = driver.find_elements(By.CSS_SELECTOR, selector)
                if articles:
                    break
            
            # If articles found, extract data
            if articles:
                for article in articles:
                    try:
                        # Title selectors in priority order
                        title_selectors = [
                            "h1 a", "h2 a", "h3 a", "h2.entry-title a", 
                            "h2", "h3", "h1", ".title a", ".title"
                        ]
                        
                        title_element = None
                        title = ""
                        link = ""
                        
                        # Find title element
                        for selector in title_selectors:
                            try:
                                title_elements = article.find_elements(By.CSS_SELECTOR, selector)
                                if title_elements:
                                    title_element = title_elements[0]
                                    title = title_element.text.strip()
                                    if title_element.tag_name == 'a':
                                        link = title_element.get_attribute("href")
                                    break
                            except StaleElementReferenceException:
                                # Retry with fresh reference
                                driver.refresh()
                                articles = driver.find_elements(By.CSS_SELECTOR, article_selectors[0])
                                continue
                        
                        # If no link found in title, try to find it separately
                        if not link and title:
                            for link_selector in ["a", ".readmore", ".more-link", ".read-more"]:
                                link_elements = article.find_elements(By.CSS_SELECTOR, link_selector)
                                if link_elements:
                                    link = link_elements[0].get_attribute("href")
                                    break
                        
                        # Extract date if available
                        date = ""
                        date_selectors = [
                            ".date", ".post-date", ".entry-date", "time", ".meta time", 
                            "span.time", ".published"
                        ]
                        for date_selector in date_selectors:
                            date_elements = article.find_elements(By.CSS_SELECTOR, date_selector)
                            if date_elements:
                                date = date_elements[0].text.strip()
                                break
                        
                        # Extract excerpt if available
                        excerpt = ""
                        excerpt_selectors = [
                            ".excerpt", ".entry-summary", ".summary", "p", ".description"
                        ]
                        for excerpt_selector in excerpt_selectors:
                            excerpt_elements = article.find_elements(By.CSS_SELECTOR, excerpt_selector)
                            if excerpt_elements:
                                excerpt = excerpt_elements[0].text.strip()
                                break
                        
                        if title and is_valid_url(link):
                            scraped_data.append({
                                "title": clean_text(title),
                                "link": link,
                                "date": date,
                                "excerpt": clean_text(excerpt),
                                "category": category,
                                "source_url": url
                            })
                    except Exception as e:
                        logger.error(f"Error extracting article content: {str(e)}")
            else:
                # Fallback for pages without clear article structure
                logger.info(f"No articles found, using fallback method for {url}")
                
                # Try to find all links that might be articles
                links = driver.find_elements(By.TAG_NAME, "a")
                for link_element in links:
                    try:
                        href = link_element.get_attribute("href")
                        link_text = link_element.text.strip()
                        
                        # Skip if link is empty, not valid, or too short to be a title
                        if not href or not link_text or len(link_text) < 10 or not is_valid_url(href):
                            continue
                            
                        # Skip navigation links, social media, etc.
                        skip_patterns = ['login', 'register', 'contact', 'about', 'facebook', 'twitter', 'instagram']
                        if any(pattern in href.lower() for pattern in skip_patterns):
                            continue
                            
                        # Get parent to check if it looks like an article container
                        parent = link_element.find_element(By.XPATH, "./..")
                        parent_class = parent.get_attribute("class") or ""
                        
                        if any(term in parent_class.lower() for term in ['post', 'article', 'entry', 'card', 'content']):
                            scraped_data.append({
                                "title": clean_text(link_text),
                                "link": href,
                                "date": "",
                                "excerpt": "",
                                "category": category,
                                "source_url": url
                            })
                    except Exception as e:
                        continue
                        
                # If still no data, just get the main content and title
                if not scraped_data:
                    try:
                        title = driver.title
                        body_text = driver.find_element(By.TAG_NAME, "body").text
                        scraped_data.append({
                            "title": clean_text(title),
                            "link": url,
                            "date": "",
                            "excerpt": clean_text(body_text[:300] + "..."),
                            "category": category,
                            "source_url": url
                        })
                    except Exception as e:
                        logger.error(f"Fallback extraction failed for {url}: {str(e)}")
            
            # Success - return scraped data
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            retries += 1
            time.sleep(random.uniform(5, 10))  # Exponential backoff
        finally:
            driver.quit()
    
    # If we get here, all retries failed
    logger.error(f"All retries failed for {url}")
    return []

def scrape_paragraphs(url, max_retries=2):
    retries = 0
    while retries <= max_retries:
        driver = set_up_driver()
        try:
            logger.info(f"Scraping content from {url}")
            driver.get(url)
            
            # Wait for page to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for page to load: {url}")
            
            # Random pause to avoid detection
            time.sleep(random.uniform(2, 5))
            
            # Try to find the article content container first
            content_selectors = [
                "article .entry-content", 
                "article .content",
                "div.entry-content",
                "div.post-content",
                "div.article-content",
                "div.content",
                "article",
                "main",
                ".main-content"
            ]
            
            content_container = None
            for selector in content_selectors:
                containers = driver.find_elements(By.CSS_SELECTOR, selector)
                if containers:
                    content_container = containers[0]
                    break
            
            # Try multiple selectors for paragraphs
            paragraph_selectors = [
                "p", 
                "div.paragraph",
                ".text"
            ]
            
            paragraphs = []
            if content_container:
                # Search within content container
                for selector in paragraph_selectors:
                    paragraphs = content_container.find_elements(By.CSS_SELECTOR, selector)
                    if paragraphs:
                        break
            else:
                # Search in entire document
                for selector in paragraph_selectors:
                    paragraphs = driver.find_elements(By.CSS_SELECTOR, selector)
                    if paragraphs:
                        break
            
            # Extract and clean paragraph texts
            paragraph_texts = []
            for p in paragraphs:
                text = p.text.strip()
                if text and len(text) > 10:  # Skip very short paragraphs
                    cleaned_text = clean_text(text)
                    if cleaned_text:
                        paragraph_texts.append(cleaned_text)
            
            # Extract metadata if available
            metadata = {}
            
            # Try to get author
            author_selectors = [".author", ".byline", ".entry-author", "meta[name='author']"]
            for selector in author_selectors:
                try:
                    author_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if author_elements:
                        metadata["author"] = author_elements[0].text.strip()
                        break
                except Exception:
                    pass
            
            # Try to get published date
            date_selectors = [
                ".date", ".published", ".post-date", ".entry-date", 
                "time", "meta[property='article:published_time']"
            ]
            for selector in date_selectors:
                try:
                    date_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if date_elements:
                        if selector.startswith("meta"):
                            metadata["published_date"] = date_elements[0].get_attribute("content")
                        else:
                            metadata["published_date"] = date_elements[0].text.strip()
                        break
                except Exception:
                    pass
            
            # If we found content, return it
            if paragraph_texts:
                content = " ".join(paragraph_texts)
                return {
                    "content": content,
                    "metadata": metadata,
                    "word_count": len(content.split()),
                    "paragraph_count": len(paragraph_texts)
                }
            elif retries < max_retries:
                # If no content found, retry
                retries += 1
                time.sleep(random.uniform(3, 7))
                continue
            else:
                # Last resort: get all text from body
                body_text = driver.find_element(By.TAG_NAME, "body").text
                cleaned_text = clean_text(body_text)
                return {
                    "content": cleaned_text,
                    "metadata": metadata,
                    "word_count": len(cleaned_text.split()),
                    "paragraph_count": 1
                }
                
        except Exception as e:
            logger.error(f"Error scraping paragraphs from {url}: {str(e)}")
            retries += 1
            time.sleep(random.uniform(5, 10))
        finally:
            driver.quit()
    
    return {
        "content": "",
        "metadata": {},
        "word_count": 0,
        "paragraph_count": 0
    }

def scrape_links(csv_file, max_workers=5):
    data = pd.read_csv(csv_file)
    detailed_data = []
    
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_row = {executor.submit(scrape_paragraphs, row['link']): row for _, row in data.iterrows()}
        
        # Process results as they complete
        for future in as_completed(future_to_row):
            row = future_to_row[future]
            try:
                result = future.result()
                if result["content"]:
                    article_data = {
                        "title": row['title'],
                        "link": row['link'],
                        "category": row['category'],
                        "date": row.get('date', ''),
                        "excerpt": row.get('excerpt', ''),
                        "source_url": row.get('source_url', ''),
                        "content": result["content"],
                        "word_count": result["word_count"],
                        "paragraph_count": result["paragraph_count"]
                    }
                    
                    # Add metadata if available
                    for key, value in result["metadata"].items():
                        if value:
                            article_data[key] = value
                    
                    detailed_data.append(article_data)
                    
                    
                    logger.info(f"Successfully scraped article: {row['title']}")
                else:
                    logger.warning(f"No content found for: {row['link']}")
            except Exception as e:
                logger.error(f"Error processing {row['link']}: {str(e)}")
    
    return detailed_data

def save_to_json(data, filename):
    """Save data to JSON with proper encoding"""
    import json
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Data saved to {filename}")

def main():
    start_time = time.time()
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Define websites with their categories
    websites = {
        "normal": [
            "https://the-indie-in-former.com/",
            "https://www.thegamer.com/tag/indie-games/",
            "https://indiegamereviewer.com/",
        ],
        "marketing": [
            "https://acorngames.gg/blog/2024/1/11/using-social-media-as-an-indie-game-developer",
            "https://enjin.io/blog/10-social-media-marketing-tips-for-indie-game-developers",
            "https://www.conduit.gg/blog/posts/best-channels-for-marketing-an-indie-game",
        ]
    }
    
    # Add ability to read websites from a config file
    try:
        if os.path.exists("scraper_config.json"):
            import json
            with open("scraper_config.json", 'r') as f:
                config = json.load(f)
                if "websites" in config:
                    websites = config["websites"]
                    logger.info("Loaded websites from configuration file")
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
    
    all_data = []
    
    # Limit concurrency to avoid getting blocked
    max_workers = 3
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for category, urls in websites.items():
            for url in urls:
                futures.append(executor.submit(scrape_website, url, category))
        
        # Process results as they complete
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    all_data.extend(result)
            except Exception as e:
                logger.error(f"Error processing scraping result: {str(e)}")
    
    # Save initial data
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv("output/scraped_data.csv", index=False)
        save_to_json(all_data, "output/scraped_data.json")
        logger.info(f"Initial scraping completed. Found {len(all_data)} articles.")
        
        # Remove duplicates based on link
        df = df.drop_duplicates(subset=['link'])
        logger.info(f"After removing duplicates: {len(df)} articles")
        
        # Scrape detailed content
        detailed_data = scrape_links("output/scraped_data.csv", max_workers=max_workers)
        
        if detailed_data:
            detailed_df = pd.DataFrame(detailed_data)
            
            # Save complete dataset
            detailed_df.to_csv("output/detailed_data.csv", index=False)
            save_to_json(detailed_data, "output/detailed_data.json")
            
            # Split and save category-specific files
            for category in detailed_df["category"].unique():
                category_df = detailed_df[detailed_df["category"] == category]
                category_df.to_csv(f"output/{category}_data.csv", index=False)
                save_to_json(category_df.to_dict('records'), f"output/{category}_data.json")
                logger.info(f"Saved {len(category_df)} articles for category: {category}")
        else:
            logger.warning("No detailed content was successfully scraped")
    else:
        logger.warning("Initial scraping did not find any articles")
    
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"Total Execution Time: {datetime.timedelta(seconds=int(total_time))}")
    
    logger.info("\nFiles created:")
    logger.info("1. output/scraped_data.csv/.json - Initial scraping results")
    logger.info("2. output/detailed_data.csv/.json - Complete dataset with full content")
    for category in websites.keys():
        logger.info(f"3. output/{category}_data.csv/.json - Data from {category} websites")
    logger.info("4. Individual article text files in scraped_articles/ directory")

if __name__ == "__main__":
    main()
    # sourceFile= "/Users/nirajdhakal/ProjectMonopoly/server/python/ai_web/output/detailed_data.json"
    # destinationFolder= "/Users/nirajdhakal/ProjectMonopoly/server/cmd/api"
    # shutil.move(sourceFile, destinationFolder)