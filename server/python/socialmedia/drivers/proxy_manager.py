
import requests
import random
import logging
import time
import json
import os
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

log = logging.getLogger(__name__)

# Path to store verified proxies
VERIFIED_PROXIES_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'verified_proxies.json')

class ProxyManager:
    """
    Manages fetching, validating, and rotating free proxies.
    
    Workflow:
        1. Every 3 hours, `validate_all_proxies()` checks ALL proxies and saves working ones.
        2. `get_working_proxy()` reads from the verified list only.
    """
    
    PROXY_SOURCES = {
        'http': 'https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/http/data.txt',
        'https': 'https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/https/data.txt',
        'socks4': 'https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/socks4/data.txt',
        'socks5': 'https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/socks5/data.txt',
        'proxyscrape': 'https://api.proxyscrape.com/v4/free-proxy-list/get?request=get_proxies&protocol=http&proxy_format=protocolipport&format=text&timeout=20000'
    }
    
    def __init__(self):
        self.proxies: List[str] = []
        self.test_url = "http://httpbin.org/ip"
        self.timeout = 5  # Seconds per proxy check
        self.max_workers = 50  # Parallel workers for validation
        
    def fetch_all_proxies(self) -> List[str]:
        """Fetch proxies from all sources."""
        log.info("🔄 Fetching proxy lists from all sources...")
        fetched = []
        
        for protocol, url in self.PROXY_SOURCES.items():
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if line and ':' in line:
                            if protocol == 'proxyscrape' or line.startswith('http'):
                                fetched.append(line)
                            elif protocol in ['http', 'https']:
                                fetched.append(f"http://{line}")
                            else:
                                fetched.append(f"{protocol}://{line}")
                                
                    log.info(f"  → Fetched {len(lines)} {protocol.upper()} proxies")
            except Exception as e:
                log.error(f"  ❌ Error fetching {protocol.upper()} list: {e}")
                
        self.proxies = list(set(fetched))
        log.info(f"✅ Total unique proxies: {len(self.proxies)}")
        return self.proxies

    def check_proxy(self, proxy_url: str) -> Optional[str]:
        """Test a single proxy. Returns the proxy URL if working, else None."""
        try:
            proxies = {"http": proxy_url, "https": proxy_url}
            response = requests.get(self.test_url, proxies=proxies, timeout=self.timeout, verify=False)
            if response.status_code == 200:
                return proxy_url
        except Exception:
            pass
        return None

    def validate_all_proxies(self) -> List[str]:
        """
        Check ALL proxies in parallel and save working ones to file.
        This should be called every 3 hours by a scheduled task.
        """
        log.info("🔍 Starting FULL proxy validation (this may take a few minutes)...")
        
        # Fetch fresh list
        self.fetch_all_proxies()
        
        if not self.proxies:
            log.warning("⚠️ No proxies to validate.")
            return []
        
        working = []
        total = len(self.proxies)
        start_time = time.time()
        
        log.info(f"   Testing {total} proxies with {self.max_workers} parallel workers...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.check_proxy, p): p for p in self.proxies}
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                result = future.result()
                if result:
                    working.append(result)
                
                # Progress logging every 500
                if completed % 500 == 0:
                    elapsed = time.time() - start_time
                    log.info(f"   Progress: {completed}/{total} checked, {len(working)} working ({elapsed:.1f}s)")
        
        elapsed = time.time() - start_time
        log.info(f"✅ Validation complete: {len(working)}/{total} working ({len(working)/total*100:.1f}%) in {elapsed:.1f}s")
        
        # Save to file
        self._save_verified_proxies(working)
        
        return working
    
    def _save_verified_proxies(self, proxies: List[str]) -> None:
        """Save verified proxies to JSON file."""
        try:
            data = {
                "verified_at": datetime.now().isoformat(),
                "count": len(proxies),
                "proxies": proxies
            }
            with open(VERIFIED_PROXIES_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            log.info(f"💾 Saved {len(proxies)} verified proxies to {VERIFIED_PROXIES_FILE}")
        except Exception as e:
            log.error(f"❌ Failed to save verified proxies: {e}")
    
    def _load_verified_proxies(self) -> List[str]:
        """Load verified proxies from JSON file."""
        try:
            if os.path.exists(VERIFIED_PROXIES_FILE):
                with open(VERIFIED_PROXIES_FILE, 'r') as f:
                    data = json.load(f)
                    proxies = data.get("proxies", [])
                    verified_at = data.get("verified_at", "unknown")
                    log.info(f"📋 Loaded {len(proxies)} verified proxies (from {verified_at})")
                    return proxies
        except Exception as e:
            log.error(f"❌ Failed to load verified proxies: {e}")
        return []

    def get_working_proxy(self) -> Optional[str]:
        """
        Get a random proxy from the verified list.
        If no verified proxies exist, returns None (fallback to local IP).
        """
        verified = self._load_verified_proxies()
        
        if verified:
            proxy = random.choice(verified)
            log.info(f"🚀 Selected proxy: {proxy} (from {len(verified)} verified)")
            return proxy
        
        log.warning("⚠️ No verified proxies available. Falling back to local IP.")
        return None
    
    def clear_verified_proxies(self) -> None:
        """Delete the verified proxies file after scraping is complete."""
        try:
            if os.path.exists(VERIFIED_PROXIES_FILE):
                os.remove(VERIFIED_PROXIES_FILE)
                log.info("🗑️ Cleared verified_proxies.json (will refresh on next validation)")
        except Exception as e:
            log.error(f"❌ Failed to clear verified proxies: {e}")

# Singleton instance
proxy_manager = ProxyManager()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Running ProxyManager independently...")
    proxy_manager.validate_all_proxies()

