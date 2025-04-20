from datetime import datetime

def generate_ai_suggestions(filename):
    return {
        "title": f"🔥 Check this out: {filename}",
        "hashtags": ["#viral", "#cool", "#funny"],
        "post_time": datetime.utcnow()
    }
