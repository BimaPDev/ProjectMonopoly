from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
from flask import Flask, request, jsonify
import random
app = Flask(__name__)
def set_up_driver():
    print("RUNNING")
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--enable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    return driver

#Function to scrape Instagram followers
def get_instagram_followers(username):
    driver = set_up_driver()
    url = f"https://www.instagram.com/{username}/"
    driver.get(url)
    time.sleep(2)  # Wait for the page to load

    try:
        followers = driver.find_element(By.XPATH, "//div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section/div[2]/ul/li[2]/div/button/span/span").text
        driver.quit()
        followers = followers.replace(",", '')
        return int(followers)
    except Exception as e:
        print(f"Error scraping Instagram followers: {e}")
        driver.quit()
        return 0

# Function to scrape Facebook followers
def get_facebook_followers(page_name):
    driver = set_up_driver()
    url = f"https://www.facebook.com/{page_name}"
    driver.get(url)
    time.sleep(2)  # Wait for the page to load

    try:
        # Locate the follower count using XPath
        followers = driver.find_element(By.XPATH, "//div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[2]/div/div/div/div[3]/div/div/div[2]/span/a[2]").text
        driver.quit()
        return parse_number(followers)
    except Exception as e:
        print(f"Error scraping Facebook followers: {e}")
        driver.quit()
        return 0


def get_linkedin_followers(company_name):
    driver = set_up_driver()
    url = f"https://www.linkedin.com/company/{company_name}"
    driver.get(url)
    time.sleep(2)  # Wait for the page to load

    try:
        followers = driver.find_element(By.XPATH, "//section[1]/section/div/div[2]/div[1]/h3").text
        driver.quit()
        followers = followers.replace("Rockville, MD", '')
        return parse_number(followers)
    except Exception as e:
        print(f"Error scraping LinkedIn followers: {e}")
        driver.quit()
        return 0



def get_twitch_followers(username):
    driver = set_up_driver()
    url = f"https://twitch.tv/{username}/about"
    driver.get(url)
    time.sleep(2)  # Wait for the page to load

    try:
        followers = driver.find_element(By.XPATH, "//div[3]/div/div/div/div[1]/div[2]/div/div/div[2]/div/div[1]/div/div/div/span/div/div/span").text
        driver.quit()
        return parse_number(followers)
    except Exception as e:
        print(f"Error scraping Twitter followers: {e}")
        driver.quit()
        return 0


def get_youtube_followers(channel_id):
    driver = set_up_driver()
    url = f"https://www.youtube.com/c/{channel_id}"
    driver.get(url)
    time.sleep(2)  # Wait for the page to load

    try:
        subscribers = driver.find_element(By.XPATH, "//yt-page-header-renderer/yt-page-header-view-model/div/div[1]/div/yt-content-metadata-view-model/div[2]/span[1]").text
        driver.quit()
        subscribers = subscribers.replace("subscribers", '')
        return parse_number(subscribers)
    except Exception as e:
        print(f"Error scraping YouTube subscribers: {e}")
        driver.quit()
        return 0

def parse_number(text):
    text = text.replace("FOLLOWERS", '')
    text = text.replace("followers", '')
    text = text.replace(",", '')
    if 'K' in text:
        text = int(text.replace('K',''))
        return text * 1000
    else:
        text = int(text)
        return text

@app.route('/followers', methods=['POST'])
def totalFollowers():
    data = request.json
    instagram_username = "dogwood_gaming"
    twitch_username = "dogwoodgaming"
    youtube_channel_id = "DogwoodGaming"
    facebook_page_name = "DogwoodGaming"
    linkedin_company_name = "dogwood-gaming"
    instagram_followers = get_instagram_followers(instagram_username)
    # twitch_followers = get_twitch_followers(twitch_username)
    # youtube_followers = get_youtube_followers(youtube_channel_id)
    # facebook_followers = get_facebook_followers(facebook_page_name)
    # linkedin_followers = get_linkedin_followers(linkedin_company_name)
    total_followers = (
                        instagram_followers
                       )
    return {total_followers}

   
# Main function
if __name__ == "__main__":

    random_port = random.randint(5000, 9999)
    app.run(debug=True, port=random_port)