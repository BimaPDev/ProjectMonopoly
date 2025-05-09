import os
import json
from datetime import datetime
import ollama

SCRAPE_DIR = "scrape_result"
FOLLOWER_ESTIMATE = 4200

# Scoring weights
CLASSIFICATION_WEIGHTS = {
    "fail": 0.8,
    "educational": 1.0,
    "cinematic": 0.9,
    "promotional": 0.6,
    "community": 0.7,
    "unknown": 0.5
}

def extract_ai_class(summary: str):
    summary = summary.lower()
    for label in CLASSIFICATION_WEIGHTS.keys():
        if label in summary:
            return label
    return "unknown"

def get_time_weight(hour):
    if 10 <= hour <= 14:
        return 1.0
    elif 1 <= hour <= 6:
        return 0.4
    return 0.7

def compute_trend_score(er, class_label, hashtag_count, hour):
    return round(
        (er * 50) +
        (CLASSIFICATION_WEIGHTS.get(class_label, 0.5) * 20) +
        (hashtag_count * 1.5) +
        (get_time_weight(hour) * 10),
        2
    )

def classify_caption(caption):
    prompt = f"""You're analyzing an Instagram FPV drone post.
Classify the style of this caption: is it cinematic, educational, a fail post, promotional, or community-focused?
Then write a short one-line summary.

Caption:
\"{caption}\""""

    try:
        response = ollama.chat(model="gemma3", messages=[
            {"role": "user", "content": prompt}
        ])
        return response['message']['content'].strip()
    except Exception as e:
        return f"Error: {e}"

def analyze_post(file_path):
    with open(file_path, "r") as f:
        post = json.load(f)

    likes = post.get("likes") or 0
    comments = post.get("comments") or 0
    hashtags = post.get("hashtags") if isinstance(post.get("hashtags"), list) else []
    caption = post.get("caption", "")
    timestamp = post.get("timestamp", "")
    username = post.get("username") or "unknown"

    try:
        engagement_rate = (likes + comments) / FOLLOWER_ESTIMATE
    except:
        engagement_rate = 0.0

    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        hour = dt.hour
    except:
        hour = -1

    ai_summary = classify_caption(caption)
    ai_class = extract_ai_class(ai_summary)
    trend_score = compute_trend_score(engagement_rate, ai_class, len(hashtags), hour)

    return {
        "username": username,
        "likes": likes,
        "comments": comments,
        "engagement_rate": round(engagement_rate, 4),
        "hashtags": hashtags,
        "post_hour": hour,
        "ai_class": ai_class,
        "trend_score": trend_score,
        "caption": caption,
        "ai_summary": ai_summary
    }

if __name__ == "__main__":
    results = []

    for file in os.listdir(SCRAPE_DIR):
        if file.endswith(".json"):
            path = os.path.join(SCRAPE_DIR, file)
            try:
                result = analyze_post(path)
                results.append(result)
                print(f"✅ Processed: {result['username']} - Score: {result['trend_score']}")
            except Exception as e:
                print(f"❌ Failed: {file} — {e}")

    with open("final_metrics.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n📄 Output saved to: final_metrics.json")
