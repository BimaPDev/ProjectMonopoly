from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import json
import os
import pickle
import re
import csv
from datetime import datetime

class InstagramScraper:
    def __init__(self, username=None, password=None, cookies_path="instagram_cookies.pkl"):
        """Initialize the Instagram scraper with optional login credentials"""
        self.username = username
        self.password = password
        self.cookies_path = cookies_path
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Set up the Chrome WebDriver with necessary options"""
        chrome_options = Options()
        # Set visible mode (not headless)
        chrome_options.headless = False
        # Add additional arguments to make the browser more stable
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        # Initialize the Chrome WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        
    def save_cookies(self):
        """Save cookies to a file for future use"""
        pickle.dump(self.driver.get_cookies(), open(self.cookies_path, "wb"))
        print("Cookies saved successfully!")
        
    def load_cookies(self):
        """Load cookies from file if available"""
        if os.path.exists(self.cookies_path):
            cookies = pickle.load(open(self.cookies_path, "rb"))
            self.driver.get("https://www.instagram.com")
            time.sleep(2)  # Wait for the page to load
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Error adding cookie: {e}")
            print("Cookies loaded successfully!")
            return True
        return False
        
    def login(self):
        """Login to Instagram using credentials or cookies"""
        # First try using saved cookies
        if self.load_cookies():
            # Refresh page after loading cookies
            self.driver.get("https://www.instagram.com")
            time.sleep(3)
            
            # Check if we're really logged in
            if "instagram.com/accounts/login" not in self.driver.current_url:
                print("Login successful using cookies!")
                return True
        
        # If cookies failed or don't exist, try username/password login
        if not self.username or not self.password:
            print("No saved cookies and no credentials provided. Cannot login.")
            return False
            
        print("Logging in with username and password...")
        self.driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)  # Wait for page to load
        
        try:
            # Accept cookies if the dialog appears
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"))
                )
                cookie_button.click()
                time.sleep(1)
            except:
                pass  # Cookie dialog may not appear
                
            # Enter username
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.send_keys(self.username)
            
            # Enter password
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(self.password)
            
            # Click login button
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            if "instagram.com/accounts/login" not in self.driver.current_url:
                print("Login successful!")
                # Save cookies for future use
                self.save_cookies()
                return True
            else:
                print("Login failed. Check your credentials.")
                return False
                
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def scrape_profile(self, profile_url, max_posts=None):
        """Scrape posts from the given Instagram profile URL"""
        if not profile_url.startswith("https://www.instagram.com/"):
            profile_url = f"https://www.instagram.com/{profile_url.strip('/')}"
            
        print(f"Navigating to profile: {profile_url}")
        self.driver.get(profile_url)
        time.sleep(3)
        
        # Get profile name for the output file
        try:
            profile_name = re.search(r"instagram\.com/([^/]+)", profile_url).group(1)
        except:
            profile_name = "instagram_profile"
            
        # Initialize list to store post data
        posts_data = []
        post_count = 0
        
        # Get all post links
        print("Finding posts...")
        post_links = []
        
        # Scroll to load more posts
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Find all post links currently visible
            try:
                post_elements = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/p/')]"))
                )
                
                # Add new post links to our list
                for element in post_elements:
                    link = element.get_attribute("href")
                    if link and link not in post_links:
                        post_links.append(link)
                        
                print(f"Found {len(post_links)} posts so far...")
                
                # Check if we've collected enough posts
                if max_posts and len(post_links) >= max_posts:
                    post_links = post_links[:max_posts]
                    break
                    
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # If heights are the same, we've probably reached the end
                    break
                last_height = new_height
                
            except Exception as e:
                print(f"Error while scrolling: {e}")
                break
                
        print(f"Found {len(post_links)} posts in total.")
        
        # Now visit each post and extract data
        for index, post_url in enumerate(post_links):
            try:
                print(f"Processing post {index+1}/{len(post_links)}: {post_url}")
                post_data = self.scrape_post(post_url)
                if post_data:
                    posts_data.append(post_data)
                    post_count += 1
                    
                # Pause between posts to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"Error processing post {post_url}: {e}")
                
        # Save the scraped data
        self.save_post_data(posts_data, profile_name)
        print(f"Scraping complete. Processed {post_count} posts.")
        return posts_data
    
    def scrape_post(self, post_url):
        """Scrape data from a single Instagram post"""
        self.driver.get(post_url)
        time.sleep(2)
        
        try:
            # Wait for the post to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//article"))
            )
            
            # Initialize post data dictionary
            post_data = {
                "url": post_url,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "caption": "",
                "likes": "",
                "comments_count": "",
                "post_date": ""
            }
            
            # Extract post date
            try:
                time_element = self.driver.find_element(By.XPATH, "//time")
                post_data["post_date"] = time_element.get_attribute("datetime")
            except:
                pass
                
            # Extract caption
            try:
                caption_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, '_a9zs')]")
                if caption_elements:
                    post_data["caption"] = caption_elements[0].text
            except:
                pass
                
            # Extract likes count
            try:
                like_elements = self.driver.find_elements(By.XPATH, "//section//span//span")
                for element in like_elements:
                    text = element.text
                    if text and text.replace(',', '').isdigit():
                        post_data["likes"] = text
                        break
            except:
                pass
                
            # Extract comments count
            try:
                comment_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/comments/')]")
                if comment_elements:
                    count_text = re.search(r"(\d+)", comment_elements[0].text)
                    if count_text:
                        post_data["comments_count"] = count_text.group(1)
            except:
                pass
                
            # Extract media URLs (images/videos)
            # try:
            #     # Try to find images
            #     img_elements = self.driver.find_elements(By.XPATH, "//article//img")
            #     for img in img_elements:
            #         src = img.get_attribute("src")
            #         if src and src not in post_data["media_urls"] and "profile_pic" not in src:
            #             post_data["media_urls"].append(src)
                        
            #     # Try to find videos
            #     video_elements = self.driver.find_elements(By.XPATH, "//article//video")
            #     for video in video_elements:
            #         src = video.get_attribute("src")
            #         if src and src not in post_data["media_urls"]:
            #             post_data["media_urls"].append(src)
            # except:
            #     pass
                
            return post_data
            
        except Exception as e:
            print(f"Error scraping post: {e}")
            return None
    
    def save_post_data(self, posts_data, profile_name):
        """Save the scraped post data to CSV and JSON files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_filename = f"{profile_name}_posts_{timestamp}.json"
        with open(json_filename, "w", encoding="utf-8") as json_file:
            json.dump(posts_data, json_file, ensure_ascii=False, indent=4)
        print(f"Saved JSON data to {json_filename}")
        
        # Save as CSV (with limited fields)
        csv_filename = f"{profile_name}_posts_{timestamp}.csv"
        with open(csv_filename, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            # Write header
            writer.writerow(["Post URL", "Date Posted", "Caption", "Likes", "Comments", "Media URLs"])
            
            # Write data rows
            for post in posts_data:
                writer.writerow([
                    post["url"],
                    post["post_date"],
                    post["caption"],
                    post["likes"],
                    post["comments_count"],
                    "; ".join(post["media_urls"])
                ])
        print(f"Saved CSV data to {csv_filename}")
    
    def close(self):
        """Close the browser and clean up"""
        if self.driver:
            self.driver.quit()


def main():
    """Main function to run the Instagram scraper"""
    print("Instagram Profile Scraper")
    print("========================")
    
    # Get Instagram credentials
    username = input("Enter your Instagram username (or press Enter to use cookies only): ")
    password = input("Enter your Instagram password (or press Enter to use cookies only): ") if username else None
    
    # Initialize the scraper
    scraper = InstagramScraper(username, password)
    
    # Login to Instagram
    if not scraper.login():
        print("Failed to login. Exiting...")
        scraper.close()
        return
    
    try:
        while True:
            # Get profile URL
            profile_url = input("\nEnter Instagram profile URL or username to scrape: ")
            if not profile_url:
                break
                
            # Get number of posts to scrape
            try:
                max_posts = input("Enter maximum number of posts to scrape (or press Enter for all): ")
                max_posts = int(max_posts) if max_posts else None
            except ValueError:
                print("Invalid number, scraping all posts.")
                max_posts = None
                
            # Scrape the profile
            scraper.scrape_profile(profile_url, max_posts)
            
            # Ask if the user wants to scrape another profile
            another = input("\nScrape another profile? (y/n): ").lower()
            if another != 'y':
                break
                
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    finally:
        # Clean up
        scraper.close()
        print("Scraping completed. Browser closed.")


if __name__ == "__main__":
    
    main()