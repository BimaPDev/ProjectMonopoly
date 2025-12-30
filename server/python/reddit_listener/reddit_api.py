"""
Reddit API Module (Public JSON Endpoints)
==========================================

Fetches Reddit data using public .json endpoints.
No authentication required.
"""

import time
import random
import logging
from datetime import datetime, timezone
from typing import Generator, Optional, Dict, Any

import requests

from .config import DEFAULT_FETCH_LIMIT, COMMENTS_FETCH_LIMIT, COMMENTS_DEPTH

log = logging.getLogger(__name__)

# Reddit requires a descriptive User-Agent or it blocks requests
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Rate limiting
BASE_DELAY = 2.0  # seconds between requests
MAX_DELAY = 60.0
MAX_RETRIES = 5


class RedditAPIClient:
    """
    Client for fetching Reddit data via public .json endpoints.
    
    No authentication required - just uses:
    - https://www.reddit.com/r/{subreddit}/new.json
    - https://www.reddit.com/search.json?q={query}
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json",
        })
        self._last_request_time = 0.0
        self._retry_count = 0
    
    def _rate_limit(self):
        """Enforce minimum delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < BASE_DELAY:
            sleep_time = BASE_DELAY - elapsed + random.uniform(0.1, 0.5)
            time.sleep(sleep_time)
        self._last_request_time = time.time()
    
    def _request_with_backoff(self, url: str, params: dict = None) -> Optional[dict]:
        """Make a request with exponential backoff on rate limits."""
        self._retry_count = 0
        
        while self._retry_count < MAX_RETRIES:
            self._rate_limit()
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                    
                elif response.status_code == 429:
                    # Rate limited
                    self._retry_count += 1
                    delay = min(BASE_DELAY * (2 ** self._retry_count), MAX_DELAY)
                    delay += random.uniform(0, delay * 0.1)  # Jitter
                    log.warning(f"Rate limited (429). Retry {self._retry_count}/{MAX_RETRIES} after {delay:.1f}s")
                    time.sleep(delay)
                    
                elif response.status_code == 403:
                    log.error(f"Forbidden (403) - Reddit may be blocking requests. URL: {url}")
                    return None
                    
                else:
                    log.error(f"HTTP {response.status_code} for {url}")
                    return None
                    
            except requests.RequestException as e:
                self._retry_count += 1
                delay = min(BASE_DELAY * (2 ** self._retry_count), MAX_DELAY)
                log.warning(f"Request error: {e}. Retry {self._retry_count}/{MAX_RETRIES} after {delay:.1f}s")
                time.sleep(delay)
        
        log.error(f"Max retries exceeded for {url}")
        return None
    
    def fetch_subreddit_new(
        self,
        subreddit: str,
        limit: int = DEFAULT_FETCH_LIMIT,
        last_seen_utc: Optional[datetime] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Fetch new posts from a subreddit.
        
        Uses: https://www.reddit.com/r/{subreddit}/new.json
        """
        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        after = None
        fetched = 0
        
        while fetched < limit:
            params = {"limit": min(100, limit - fetched)}
            if after:
                params["after"] = after
            
            data = self._request_with_backoff(url, params)
            if not data or "data" not in data:
                break
            
            children = data["data"].get("children", [])
            if not children:
                break
            
            for child in children:
                if child["kind"] != "t3":  # t3 = post
                    continue
                    
                post_data = child["data"]
                created_utc = datetime.fromtimestamp(post_data["created_utc"], tz=timezone.utc)
                
                # Stop if we've seen this post before
                if last_seen_utc and created_utc <= last_seen_utc:
                    log.debug(f"Reached already-seen post at {created_utc}")
                    return
                
                fetched += 1
                yield self._normalize_post(post_data)
                
                if fetched >= limit:
                    break
            
            # Pagination
            after = data["data"].get("after")
            if not after:
                break
    
    def fetch_search(
        self,
        query: str,
        subreddit: Optional[str] = None,
        limit: int = DEFAULT_FETCH_LIMIT,
        last_seen_utc: Optional[datetime] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search Reddit for posts matching a query.
        
        Uses: https://www.reddit.com/search.json?q={query}
        """
        if subreddit:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {"q": query, "restrict_sr": "on", "sort": "new", "limit": min(100, limit)}
        else:
            url = "https://www.reddit.com/search.json"
            params = {"q": query, "sort": "new", "limit": min(100, limit)}
        
        after = None
        fetched = 0
        
        while fetched < limit:
            if after:
                params["after"] = after
            
            data = self._request_with_backoff(url, params)
            if not data or "data" not in data:
                break
            
            children = data["data"].get("children", [])
            if not children:
                break
            
            for child in children:
                if child["kind"] != "t3":
                    continue
                    
                post_data = child["data"]
                created_utc = datetime.fromtimestamp(post_data["created_utc"], tz=timezone.utc)
                
                if last_seen_utc and created_utc <= last_seen_utc:
                    return
                
                fetched += 1
                yield self._normalize_post(post_data)
                
                if fetched >= limit:
                    break
            
            after = data["data"].get("after")
            if not after:
                break
    
    def fetch_comments_for_submission(
        self,
        submission_id: str,
        limit: int = COMMENTS_FETCH_LIMIT,
        depth: int = COMMENTS_DEPTH,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Fetch top comments for a submission.
        
        Uses: https://www.reddit.com/comments/{id}.json
        """
        # Clean submission_id (remove t3_ prefix if present)
        clean_id = submission_id.replace("t3_", "")
        url = f"https://www.reddit.com/comments/{clean_id}.json"
        
        params = {"limit": limit, "depth": depth, "sort": "top"}
        
        data = self._request_with_backoff(url, params)
        if not data or len(data) < 2:
            return
        
        # data[0] = post, data[1] = comments
        comments_data = data[1].get("data", {}).get("children", [])
        
        count = 0
        for child in comments_data:
            if child["kind"] != "t1":  # t1 = comment
                continue
            
            comment_data = child["data"]
            if comment_data.get("body") in ("[removed]", "[deleted]"):
                continue
            
            count += 1
            yield self._normalize_comment(comment_data)
            
            if count >= limit:
                break
    
    def _normalize_post(self, data: dict) -> Dict[str, Any]:
        """Convert raw Reddit post data to our standard format."""
        return {
            "external_id": f"t3_{data['id']}",
            "external_url": f"https://reddit.com{data.get('permalink', '')}",
            "subreddit": data.get("subreddit", ""),
            "title": data.get("title", ""),
            "body": data.get("selftext", ""),
            "author": data.get("author", "[deleted]"),
            "author_flair": data.get("author_flair_text"),
            "score": data.get("score", 0),
            "num_comments": data.get("num_comments", 0),
            "created_utc": datetime.fromtimestamp(data["created_utc"], tz=timezone.utc),
            "nsfw": data.get("over_18", False),
            "removed": data.get("removed_by_category") is not None,
            "raw_json": data,
        }
    
    def _normalize_comment(self, data: dict) -> Dict[str, Any]:
        """Convert raw Reddit comment data to our standard format."""
        return {
            "external_id": f"t1_{data['id']}",
            "parent_external_id": data.get("parent_id"),
            "body": data.get("body", ""),
            "author": data.get("author", "[deleted]"),
            "author_flair": data.get("author_flair_text"),
            "score": data.get("score", 0),
            "created_utc": datetime.fromtimestamp(data["created_utc"], tz=timezone.utc),
            "removed": data.get("body") in ("[removed]", "[deleted]"),
            "raw_json": data,
        }


# Singleton client
_client: Optional[RedditAPIClient] = None


def get_client() -> RedditAPIClient:
    """Get the singleton Reddit client."""
    global _client
    if _client is None:
        _client = RedditAPIClient()
    return _client
