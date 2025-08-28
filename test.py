# pip install playwright vaderSentiment beautifulsoup4
# python -m playwright install chromium
import json, re, time
from collections import Counter, defaultdict
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from playwright.sync_api import sync_playwright
import os, json, tempfile, subprocess, math, re
import numpy as np
import cv2
import librosa
from yt_dlp import YoutubeDL

HASHTAG_RE = re.compile(r"#\w+")
HEADLESS = False
SESSION_ID = "bc4ec3b8a57a7d89a3497c14ba4a683c"
# put near top
def parse_compact_num(s: str):
    if not s: return None
    s = s.strip().upper().replace(",","")
    m = re.match(r"^([0-9]*\.?[0-9]+)\s*([KMB]?)$", s)
    if not m: 
        try: return int(s)
        except: return None
    val, suf = float(m.group(1)), m.group(2)
    mult = {"":1, "K":1_000, "M":1_000_000, "B":1_000_000_000}[suf]
    return int(val * mult)

def make_ctx_with_session(browser):
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    ctx = browser.new_context(locale="en-US", user_agent=ua, viewport={"width":1280,"height":900})
    ctx.add_cookies([
        {"name":"sessionid","value":SESSION_ID,"domain":".tiktok.com","path":"/","httpOnly":True,"secure":True,"sameSite":"Lax"},
        {"name":"sessionid_ss","value":SESSION_ID,"domain":".tiktok.com","path":"/","httpOnly":True,"secure":True,"sameSite":"Lax"},
    ])
    return ctx

def get_comments_playwright(url:str, max_comments=200, timeout_s=60):
    out = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        ctx = make_ctx_with_session(browser)
        page = ctx.new_page()

        print("    [comments] Warm-up…")
        page.goto("https://www.tiktok.com/", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)

        print("    [comments] Load video…")
        page.goto(url.split("?")[0], wait_until="domcontentloaded", timeout=timeout_s*1000)
        page.wait_for_load_state("networkidle", timeout=15000)

        # Accept cookies if shown
        for sel in ["button:has-text('Accept')", "button:has-text('I agree')"]:
            try: page.locator(sel).first.click(timeout=2000)
            except: pass

        # Click the Comments button (several fallbacks)
        btn_sels = [
            "[data-e2e='browse-video-comments']",
            "button[aria-label*='omments']",
            "button:has-text('Comments')",
            "role=button[name=/comments/i]",
            "xpath=/html/body//article//section//button[.//text()[contains(.,'Comments')]]",
        ]
        clicked = False
        for sel in btn_sels:
            try:
                btn = page.locator(sel).first
                btn.wait_for(state="visible", timeout=8000)
                btn.scroll_into_view_if_needed(timeout=2000)
                try: btn.click(timeout=2000)
                except: page.evaluate("(el)=>el.click()", btn.element_handle())
                clicked = True
                break
            except: 
                continue
        if not clicked:
            print("    [comments] Button not found; screenshot -> /tmp/tt_btn.png")
            try: page.screenshot(path="/tmp/tt_btn.png", full_page=True)
            except: pass
            browser.close()
            return []

        # Wait for any comment item to appear (robust selector)
        try:
            page.wait_for_selector("[data-e2e='comment-item'], aside [data-e2e='comment-item']", timeout=timeout_s*1000)
        except:
            print("    [comments] Items not found; screenshot -> /tmp/tt_items.png")
            try: page.screenshot(path="/tmp/tt_items.png", full_page=True)
            except: pass
            browser.close()
            return []

        # Find the scrollable comments container by heuristics
        cont = None
        for sel in [
            "aside section div:has([data-e2e='comment-item'])",    # desktop
            "[data-e2e='comment-list']",                           # if present
            "aside div[role='list']",                               # ARIA list
            "aside",                                                # fallback
        ]:
            loc = page.locator(sel)
            if loc.count():
                cont = loc.first
                break
        if cont is None:
            cont = page.locator("body")

        print("    [comments] Scrolling…")
        start = time.time()
        last_n = -1
        while len(out) < max_comments and (time.time()-start) < timeout_s:
            try:
                page.evaluate("(el)=>el.scrollBy(0, 2000)", cont.element_handle())
            except: 
                page.mouse.wheel(0, 2000)
            time.sleep(0.35)

            # Pull current batch
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("[data-e2e='comment-item']")
            tmp = []
            for it in items:
                a = it.select_one("[data-e2e='comment-username']")
                author = a.get_text(strip=True) if a else None
                t = it.select_one("[data-e2e='comment-level-1']") or it.select_one("p, span")
                text = t.get_text(" ", strip=True) if t else None
                lk = it.select_one("[data-e2e='comment-like-count']") or it.select_one("button, span")
                likes = parse_compact_num(lk.get_text(strip=True)) if lk else None
                ts = it.select_one("span[data-e2e='comment-time']")
                ts = ts.get_text(strip=True) if ts else None
                if text:
                    tmp.append({"author": author, "text": text, "likes": likes, "time": ts})
            out = tmp

            if len(out) % 25 == 0:
                print(f"    [comments] Collected {len(out)}…")

            if len(out) == last_n:
                # deep scroll once more
                try: page.evaluate("(el)=>el.scrollTo(0, el.scrollHeight)", cont.element_handle())
                except: pass
                time.sleep(0.6)
                if len(out) == last_n:
                    break
            last_n = len(out)

        browser.close()
    return out[:max_comments]


def extract_music_fields(info:dict):
    # yt-dlp sometimes exposes these on TikTok
    music = {}
    for k in ("track","artist","album","alt_title","creator","music","music_id","uploader","uploader_id"):
        if k in info and info[k]:
            music[k] = info[k]
    # Best-effort normalization
    title = music.get("track") or music.get("alt_title") or music.get("music")
    artist = music.get("artist") or music.get("creator")
    return {"title": title, "artist": artist, "raw": music or None}

def hashtag_stats(caption:str, comments:list):
    tags = [t.lower() for t in HASHTAG_RE.findall(caption or "")]
    for c in comments:
        tags += [t.lower() for t in HASHTAG_RE.findall(c.get("text",""))]
    freq = Counter(tags)
    diversity = len(freq)
    total = sum(freq.values())
    top = freq.most_common(10)
    # co-occurrence matrix for top 10
    co = defaultdict(Counter)
    # per-comment set to avoid double counting within one comment
    for c in comments + [{"text": caption or ""}]:
        present = list({t.lower() for t in HASHTAG_RE.findall(c.get("text",""))})
        for i, a in enumerate(present):
            for b in present[i+1:]:
                co[a][b] += 1
                co[b][a] += 1
    return {
        "total_tags": total,
        "unique_tags": diversity,
        "top10": top,
        "co_occurrence": {k: dict(v) for k,v in co.items() if k in dict(top)}
    }

def comment_metrics(comments:list):
    sia = SentimentIntensityAnalyzer()
    if not comments:
        return {
            "count": 0,
            "avg_sentiment": None,
            "pos_share": None,
            "neg_share": None,
            "neu_share": None,
            "avg_comment_likes": None,
            "topic_counts": {},          # <-- add this
            "top_comments": []
        }

    scores = [sia.polarity_scores(c["text"])["compound"] for c in comments]
    pos = sum(1 for s in scores if s >= 0.05)
    neg = sum(1 for s in scores if s <= -0.05)
    neu = len(scores) - pos - neg
    avg_likes = sum((c.get("likes") or 0) for c in comments)/len(comments)

    # simple topic seeds via keyword counts
    kw = {
        "funny":["lol","lmao","funny","😂","🤣"],
        "relatable":["same","fr","me","relate","mood"],
        "trend":["trend","audio","sound","capcut","template"],
        "quality":["camera","lighting","edit","color","cinematic"],
        "cta":["follow","part 2","like","share","link"],
    }
    topics = {k:0 for k in kw}
    for c in comments:
        t = c["text"].lower()
        for k, words in kw.items():
            if any(w in t for w in words):
                topics[k]+=1

    top_comments = sorted(comments, key=lambda x:(x.get("likes") or 0), reverse=True)[:5]
    return {
        "count": len(comments),
        "avg_sentiment": round(sum(scores)/len(scores),3),
        "pos_share": round(pos/len(scores),3),
        "neg_share": round(neg/len(scores),3),
        "neu_share": round(neu/len(scores),3),
        "avg_comment_likes": round(avg_likes,2),
        "topic_counts": topics,
        "top_comments": top_comments
    }

# --- integrate into analyze() output ---
def analyze_plus(url:str, max_comments=200):
    print("[1/8] Downloading TikTok video & metadata...")
    info, path = get_tiktok(url)

    print("[2/8] Analyzing visuals...")
    visual = scene_metrics(path)

    print("[3/8] Analyzing audio...")
    audio = audio_metrics(path)

    print("[4/8] Transcribing speech (Whisper)...")
    speech = try_transcript(path)

    print("[5/8] Extracting caption/hashtags/music info...")
    caption = info.get("description") or info.get("title") or ""
    hashtags = [h for h in HASHTAG_RE.findall(caption)]
    eng = derive_engagement(info)
    music = extract_music_fields(info)

    print(f"[6/8] Scraping up to {max_comments} comments...")
    comments = []
    try:
        comments = get_comments_playwright(url, max_comments=max_comments)
    except Exception as e:
        print(f"    Comment scrape failed: {e}")

    print("[7/8] Processing hashtag & comment metrics...")
    hstats = hashtag_stats(caption, comments)
    cstats = comment_metrics(comments)

    print("[8/8] Cleaning up & compiling results...")
    try: os.remove(path)
    except: pass

    return {
        "source": {...},
        "metrics": {...},
        "why_it_might_work": [...]
    }

    return {
        "source": {
            "url": url,
            "id": info.get("id"),
            "uploader": info.get("uploader"),
            "upload_date": info.get("upload_date"),
            "duration_s": info.get("duration"),
            "caption": caption,
            "hashtags_in_caption": hashtags,
            "music": music
        },
        "metrics": {
            "engagement": eng,
            "visual": visual,
            "audio": audio,
            "speech": speech,
            "comments": cstats,
            "hashtags": hstats
        },
        "why_it_might_work": [
            # extend heuristics with social proof signals
            "high early hook loudness" if audio["hook_loudness_ratio_0_3s"]>1.15 else None,
            "dense cutting" if visual["cuts_per_min"]>=20 else None,
            "positive comment skew" if (cstats["avg_sentiment"] or 0)>0.15 else None,
            "comment topics: funny/relatable" if any(cstats["topic_counts"].get(k,0)>0 for k in ["funny","relatable"]) else None,
            "popular template/audio" if "trend" in [k for k,v in cstats["topic_counts"].items() if v>0] else None,
            "hashtag breadth > 5" if hstats["unique_tags"]>5 else None,
        ]
    }
    
def get_tiktok(url:str):
    ydl_opts = {
        "quiet": True,
        "skip_download": False,
        "outtmpl": "%(id)s.%(ext)s",
        "format": "mp4",
        "noplaylist": True,
        "retries": 5,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
    return info, path

def scene_metrics(video_path:str, sample_rate_fps=6, cut_thresh=0.35, max_samples=800):
    print("    [scene_metrics] Opening video...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("    [scene_metrics] OpenCV failed, falling back to ffmpeg...")
        return _scene_metrics_ffmpeg(video_path, sample_rate_fps, cut_thresh, max_samples)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    print(f"    [scene_metrics] FPS={fps}, Total frames={total_frames}")

    duration = total_frames / max(fps,1)
    step = max(int(fps // sample_rate_fps), 1)

    prev = None
    cuts = 0
    motion_scores, brightness, colorfulness = [], [], []
    processed = 0
    prev_hist = None

    for i in range(0, total_frames, step):
        if processed >= max_samples:
            print("    [scene_metrics] Reached max sample limit")
            break
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, frame = cap.read()
        if not ok:
            print(f"    [scene_metrics] Frame {i} read failed")
            break
        processed += 1
        if processed % 50 == 0:
            print(f"    [scene_metrics] Processed {processed} frames...")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness.append(float(gray.mean()))

        if prev is not None:
            diff = cv2.absdiff(gray, prev)
            motion_scores.append(float(diff.mean()))
        prev = gray

        b, g, r = cv2.split(frame.astype(np.float32))
        rg = np.abs(r - g)
        yb = np.abs(0.5*(r+g) - b)
        cf = math.sqrt(np.std(rg)**2 + np.std(yb)**2) + 0.3*math.sqrt(np.mean(rg)**2 + np.mean(yb)**2)
        colorfulness.append(float(cf))

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv],[0,1],None,[50,50],[0,180,0,256])
        hist = cv2.normalize(hist, hist).flatten()
        if prev_hist is not None:
            d = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
            if d > cut_thresh:
                cuts += 1
        prev_hist = hist

    cap.release()
    print("    [scene_metrics] Done.")

    return {
        "duration_s": round(duration,2),
        "avg_brightness": round(float(np.mean(brightness)) if brightness else 0,2),
        "avg_colorfulness": round(float(np.mean(colorfulness)) if colorfulness else 0,2),
        "motion_mean": round(float(np.mean(motion_scores)) if motion_scores else 0,2),
        "scene_cuts": int(cuts),
        "cuts_per_min": round(cuts / (duration/60) if duration>0 else 0,2),
        "samples_used": processed,
        "method": "opencv",
    }

def audio_metrics(video_path:str):
    # extract audio to wav
    wav = tempfile.mktemp(suffix=".wav")
    subprocess.run([
        "ffmpeg","-y","-i",video_path,"-vn","-ac","1","-ar","16000",wav
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    y, sr = librosa.load(wav, sr=16000, mono=True)
    rms = float(np.sqrt(np.mean(y**2)))
    loudness_db = 20*np.log10(max(rms, 1e-8))
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    # simple “hook” proxy: average amplitude in first 3 s vs rest
    n3 = min(len(y), 3*sr)
    hook_amp = float(np.mean(np.abs(y[:n3]))) if n3>0 else 0.0
    rest_amp = float(np.mean(np.abs(y[n3:]))) if len(y)>n3 else hook_amp
    hook_ratio = hook_amp / max(rest_amp,1e-6)

    os.remove(wav)
    return {
        "loudness_dbFS": round(loudness_db,2),
        "tempo_bpm_est": round(float(tempo),1),
        "hook_loudness_ratio_0_3s": round(hook_ratio,2),
    }

def try_transcript(video_path:str):
    try:
        import whisper
        model = whisper.load_model("base")
        t = model.transcribe(video_path, fp16=False)
        text = t.get("text","").strip()
        wpm = 0
        if t.get("segments"):
            duration = t["segments"][-1]["end"]
            words = len(re.findall(r"\w+", text))
            wpm = 60*words/max(duration,1)
        return {"transcript": text, "speech_rate_wpm": round(wpm,1)}
    except Exception:
        return {"transcript": None, "speech_rate_wpm": None}

def derive_engagement(info:dict):
    # Depends on availability; TikTok often hides some fields. Use if present.
    stats = {}
    for k in ["view_count","like_count","comment_count","repost_count","repost_view_count","repost_like_count","repost_comment_count","repost_repost_count","average_rating"]:
        if k in info: stats[k]=info[k]
    views = info.get("view_count") or None
    likes = info.get("like_count") or 0
    comments = info.get("comment_count") or 0
    shares = info.get("repost_count") or 0
    er = (likes+comments+shares)/views if views and views>0 else None
    return {
        "views": views, "likes": likes, "comments": comments, "shares": shares,
        "engagement_rate": round(er,4) if er is not None else None
    }

def analyze_plus(url:str, max_comments=200):
    print("[1/8] Downloading TikTok video & metadata...")
    info, path = get_tiktok(url)

    print("[2/8] Analyzing visuals...")
    visual = scene_metrics(path)

    print("[3/8] Analyzing audio...")
    audio = audio_metrics(path)

    print("[4/8] Transcribing speech (Whisper)...")
    speech = try_transcript(path)

    print("[5/8] Extracting caption/hashtags/music info...")
    caption = info.get("description") or info.get("title") or ""
    hashtags = [h for h in HASHTAG_RE.findall(caption)]
    eng = derive_engagement(info)
    music = extract_music_fields(info)

    print(f"[6/8] Scraping up to {max_comments} comments...")
    try:
        comments = get_comments_playwright(url, max_comments=max_comments)
    except Exception as e:
        print(f"    Comment scrape failed: {e}")
        comments = []

    print("[7/8] Processing hashtag & comment metrics...")
    hstats = hashtag_stats(caption, comments)
    cstats = comment_metrics(comments)

    print("[8/8] Cleaning up & compiling results...")
    try: os.remove(path)
    except: pass

    return {
        "source": {
            "url": url,
            "id": info.get("id"),
            "uploader": info.get("uploader"),
            "upload_date": info.get("upload_date"),
            "duration_s": info.get("duration"),
            "caption": caption,
            "hashtags_in_caption": hashtags,
            "music": music
        },
        "metrics": {
            "engagement": eng,
            "visual": visual,
            "audio": audio,
            "speech": speech,
            "comments": cstats,
            "hashtags": hstats
        },
        "why_it_might_work": list(filter(None, [
            "high early hook loudness" if audio["hook_loudness_ratio_0_3s"]>1.15 else None,
            "dense cutting" if visual["cuts_per_min"]>=20 else None,
            "positive comment skew" if (cstats["avg_sentiment"] or 0)>0.15 else None,
            "comment topics: funny/relatable" if any(cstats["topic_counts"].get(k,0)>0 for k in ["funny","relatable"]) else None,
            "popular template/audio" if cstats["topic_counts"].get("trend",0)>0 else None,
            "hashtag breadth > 5" if hstats["unique_tags"]>5 else None,
        ]))
    }

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Paste TikTok URL: ").strip()
    results = analyze_plus(url, max_comments=200)
    print(json.dumps(results, indent=2, ensure_ascii=False))