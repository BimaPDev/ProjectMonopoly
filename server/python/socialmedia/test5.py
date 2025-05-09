import os
import json
import csv
from collections import Counter
from datetime import datetime
import ollama

SCRAPE_DIR = "scrape_result"
FOLLOWER_ESTIMATE = 4200  # Default fallback

def load_posts(scrape_dir):
    posts = []
    for file in os.listdir(scrape_dir):
        if file.endswith(".json"):
            path = os.path.join(scrape_dir, file)
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    posts.append(data)
            except Exception as e:
                print(f"❌ Failed to load {file}: {e}")
    return posts

def analyze_post(post, follower_count=None):
    result = {}

    result['username'] = post.get('username') or 'unknown'
    result['likes'] = post.get('likes') or 0
    result['comments'] = post.get('comments') or 0

    hashtags = post.get('hashtags')
    result['hashtags'] = hashtags if isinstance(hashtags, list) else []

    result['timestamp'] = post.get('timestamp') or ''
    result['caption'] = post.get('caption', '')

    # Engagement rate
    try:
        result['engagement_rate'] = (result['likes'] + result['comments']) / follower_count
    except:
        result['engagement_rate'] = 0.0

    # Posting hour
    try:
        dt = datetime.fromisoformat(result['timestamp'].replace("Z", "+00:00"))
        result['post_hour'] = dt.hour
    except Exception:
        result['post_hour'] = -1

    return result

def classify_caption_with_gemma(caption):
    prompt = f"""You're analyzing an Instagram FPV drone post.
Classify the style of this caption: is it cinematic, educational, a fail post, or something else?
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

def aggregate_results(all_results):
    hashtags = Counter()
    hours = Counter()
    for r in all_results:
        hashtags.update(r['hashtags'])
        if r['post_hour'] >= 0:
            hours[r['post_hour']] += 1
    return {
        'top_hashtags': hashtags.most_common(5),
        'common_post_hour': hours.most_common(1)[0][0] if hours else None
    }

# MAIN
if __name__ == "__main__":
    posts = load_posts(SCRAPE_DIR)
    print(f"📦 Loaded {len(posts)} scraped post(s)")

    all_results = []
    for post in posts:
        result = analyze_post(post, FOLLOWER_ESTIMATE)
        result['ai_summary'] = classify_caption_with_gemma(result['caption'])
        all_results.append(result)

        print(f"\n📄 @{result['username']} — {result['engagement_rate']:.2%} ER at hour {result['post_hour']}")
        print("🧠 Gemma:", result['ai_summary'])

    # Aggregated summary
    agg = aggregate_results(all_results)
    print("\n📊 Aggregated Insights:")
    print("=" * 30)
    print("Top Hashtags:")
    for tag, count in agg['top_hashtags']:
        print(f"  {tag}: {count}x")
    print("Most Common Posting Hour:", agg['common_post_hour'] or "N/A")

    # Export to JSON
    with open("output_summary.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("📄 JSON export: output_summary.json")

    # Export to CSV
    with open("output_summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_results[0].keys()))
        writer.writeheader()
        writer.writerows(all_results)
    print("📄 CSV export: output_summary.csv")
