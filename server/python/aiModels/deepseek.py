import requests
import json

# Replace 'YOUR_API_KEY' with your actual DeepSeek API key
API_KEY = 'YOUR_API_KEY'
API_URL = 'https://api.deepseek.com/chat/completions'

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}

def get_deepseek_response(prompt):
    """Fetches a response from the DeepSeek API based on the given prompt."""
    data = {
        'model': 'deepseek-chat',  # Specifies the DeepSeek V3 model
        'messages': [
            {'role': 'system', 'content': 'You are a helpful code reviewer.'},
            {'role': 'user', 'content': prompt}
        ],
        'stream': False  # Set to True for streaming responses
    }

    response = requests.post(API_URL, headers=HEADERS, data=json.dumps(data))

    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")