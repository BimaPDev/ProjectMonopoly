import requests

def get_instagram_followers(access_token, user_id):
    url = f"https://graph.facebook.com/v17.0/{user_id}?fields=followers_count&access_token={access_token}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('followers_count', 0)
    print(f"Error fetching Instagram followers: {response.json()}")
    return 0

def get_twitter_followers(bearer_token, username):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_id = response.json().get('data', {}).get('id')
        if user_id:
            user_url = f"https://api.twitter.com/2/users/{user_id}?user.fields=public_metrics"
            user_response = requests.get(user_url, headers=headers)
            if user_response.status_code == 200:
                return user_response.json().get('data', {}).get('public_metrics', {}).get('followers_count', 0)
    print(f"Error fetching Twitter followers: {response.json()}")
    return 0

def get_youtube_followers(api_key, channel_id):
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel_id}&key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return int(response.json()['items'][0]['statistics']['subscriberCount'])
    print(f"Error fetching YouTube subscribers: {response.json()}")
    return 0

# Replace with your API keys and account details
instagram_access_token = "your_instagram_access_token"
instagram_user_id = "your_instagram_user_id"
twitter_bearer_token = "your_twitter_bearer_token"
twitter_username = "your_twitter_username"
youtube_api_key = "your_youtube_api_key"
youtube_channel_id = "your_youtube_channel_id"

instagram_followers = get_instagram_followers(instagram_access_token, instagram_user_id)
twitter_followers = get_twitter_followers(twitter_bearer_token, twitter_username)
youtube_followers = get_youtube_followers(youtube_api_key, youtube_channel_id)

total_followers = instagram_followers + twitter_followers + youtube_followers
print(f"Total Followers: {total_followers}")
