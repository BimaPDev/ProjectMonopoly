import json
import pandas as pd
from datetime import datetime

# === Config ===
file_paths = [
    "test.json",
]
output_csv = "post_analytics_output.csv"

# === Load JSON ===
def load_json(paths):
    data = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            data.extend(json.load(f))
    return data

# === Preprocess Posts ===
def preprocess(posts):
    for post in posts:
        post['likes'] = int(post['likes']) if post['likes'].isdigit() else 0
        post['comments_count'] = int(post['comments_count']) if post['comments_count'].isdigit() else 0
        post['engagement'] = post['likes'] + post['comments_count']
        post['post_date'] = datetime.fromisoformat(post['post_date'].replace("Z", "+00:00"))
        post['weekday'] = post['post_date'].strftime('%A')
        post['hour'] = post['post_date'].hour
        post['num_hashtags'] = len(post['hashtags']) if isinstance(post['hashtags'], list) else 0
    return posts

# === Analyze ===
def analyze(df):
    return {
        "average_likes": df['likes'].mean(),
        "average_comments": df['comments_count'].mean(),
        "average_engagement": df['engagement'].mean(),
        "top_post_url": df.sort_values(by='engagement', ascending=False).iloc[0]['url'],
        "best_day_to_post": df.groupby('weekday')['engagement'].mean().idxmax(),
        "best_hour_to_post": df.groupby('hour')['engagement'].mean().idxmax(),
        "top_hashtags": df.explode('hashtags')['hashtags'].value_counts().head(10).to_dict()
    }

# === Run Script ===
data = preprocess(load_json(file_paths))
df = pd.DataFrame(data)
summary = analyze(df)

# Save as CSV
df.to_csv(output_csv, index=False)

# Output summary
print("✅ ANALYSIS SUMMARY")
for k, v in summary.items():
    print(f"{k}: {v}")
print(f"\nCSV saved to: {output_csv}")
