import json
from collections import Counter, defaultdict

INPUT_FILE = "final_metrics.json"

def load_data(path):
    with open(path, "r") as f:
        return json.load(f)

def top_hashtags(posts, top_n=5):
    tags = Counter()
    for p in posts:
        tags.update(p.get("hashtags", []))
    return tags.most_common(top_n)

def best_post_hours(posts, top_n=3):
    hours = Counter()
    for p in posts:
        hour = p.get("post_hour")
        if hour != -1:
            hours[hour] += 1
    return [h for h, _ in hours.most_common(top_n)]

def engagement_by_type(posts):
    type_buckets = defaultdict(list)
    for p in posts:
        ai_class = p.get("ai_class", "unknown")
        type_buckets[ai_class].append(p.get("engagement_rate", 0.0))

    avg_er_by_type = {
        t: round(sum(vals)/len(vals), 4)
        for t, vals in type_buckets.items() if vals
    }

    return sorted(avg_er_by_type.items(), key=lambda x: -x[1])

def top_posts(posts, top_n=3):
    sorted_posts = sorted(posts, key=lambda x: -x.get("trend_score", 0))
    return sorted_posts[:top_n]

def generate_report(posts):
    hashtags = top_hashtags(posts)
    hours = best_post_hours(posts)
    er_types = engagement_by_type(posts)
    top = top_posts(posts)

    report = []
    report.append("📊 FPV Social Media Insights Report\n" + "="*40)
    report.append(f"\n✅ Best Times to Post:\n" + "\n".join([f" - {h}:00" for h in hours]))

    report.append("\n🔥 Top Hashtags:")
    for tag, count in hashtags:
        report.append(f" - {tag} ({count} uses)")

    report.append("\n🧠 Top Content Types by Avg Engagement:")
    for t, er in er_types:
        report.append(f" - {t.capitalize()} → {er:.2%} ER")

    report.append("\n🏆 Top Performing Posts:")
    for p in top:
        report.append(f" - @{p['username']} (Score: {p['trend_score']})")
        report.append(f"   Caption: {p['caption'][:80]}...")

    return "\n".join(report)

if __name__ == "__main__":
    posts = load_data(INPUT_FILE)
    report = generate_report(posts)

    # Print to terminal
    print(report)

    # Save to file
    with open("insight_report.txt", "w") as f:
        f.write(report)

    print("\n📄 Saved to insight_report.txt")
