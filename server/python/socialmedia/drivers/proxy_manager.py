
import requests
import random
import logging
import time
from typing import Optional, List, Dict
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

class ProxyManager:
    """
    Manages fetching, validating, and rotating free proxies from GitHub lists.
    Supports HTTP, SOCKS4, and SOCKS5.
    """
    
    PROXY_SOURCES = {
        'http': 'https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/http/data.txt',
        'https': 'https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/https/data.txt',
        'socks4': 'https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/socks4/data.txt',
        'socks5': 'https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/socks5/data.txt'
    }
    
    def __init__(self):
        self.proxies: List[str] = []
        self.last_fetch_time: Optional[datetime] = None
        self.cache_duration = timedelta(hours=1)
        self.test_url = "http://httpbin.org/ip" # Lightweight endpoint for validation
        self.timeout = 5 # Seconds
        
    def refresh_proxies(self, force: bool = False) -> None:
        """
        Fetch proxies from all sources.
        
        Args:
            force: If True, bypass cache duration and force fresh fetch.
        """
        if not force and self.proxies and self.last_fetch_time and (datetime.now() - self.last_fetch_time < self.cache_duration):
            return

        log.info("🔄 Fetching fresh proxy lists...")
        fetched_proxies = []
        
        for protocol, url in self.PROXY_SOURCES.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    # Format: ip:port (raw list usually just has ip:port)
                    # We need to prepend protocol for requests/selenium usage
                    # e.g. 1.2.3.4:8080 -> http://1.2.3.4:8080 or socks5://1.2.3.4:1080
                    
                    for line in lines:
                        line = line.strip()
                        if line and ':' in line:
                            # Add protocol prefix
                            if protocol in ['http', 'https']:
                                # HTTP/HTTPS proxies both use http:// scheme for connection in most libs (requests/selenium)
                                fetched_proxies.append(f"http://{line}")
                            else:
                                fetched_proxies.append(f"{protocol}://{line}")
                                
                    log.info(f"  → Fetched {len(lines)} {protocol.upper()} proxies")
                else:
                    log.warning(f"  ❌ Failed to fetch {protocol.upper()} list: Status {response.status_code}")
            except Exception as e:
                log.error(f"  ❌ Error fetching {protocol.upper()} list: {e}")
                
        self.proxies = list(set(fetched_proxies)) # Deduplicate
        self.last_fetch_time = datetime.now()
        log.info(f"✅ Total unique proxies available: {len(self.proxies)}")

    def check_proxy(self, proxy_url: str) -> bool:
        """
        Validate a proxy by making a request to a test endpoint.
        Returns True if connection succeeds within timeout.
        """
        try:
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            # verify=False to avoid SSL cert issues with free proxies
            response = requests.get(self.test_url, proxies=proxies, timeout=self.timeout, verify=False)
            if response.status_code == 200:
                log.debug(f"  ✅ Proxy working: {proxy_url}")
                return True
        except Exception:
            pass # Silent failure for invalid proxies
            
        return False

    def get_working_proxy(self, max_retries: int = 3) -> Optional[str]:
        """
        Get a verified working proxy.
        Tries random proxies from the list up to max_retries times.
        Returns None if no working proxy is found (caller should fallback to local).
        """
        self.refresh_proxies()
        
        if not self.proxies:
            log.warning("⚠️ No proxies available in list.")
            return None
            
        log.info(f"🔍 Searching for a working proxy (max {max_retries} attempts)...")
        
        # shuffle to ensure randomness
        candidates = random.sample(self.proxies, min(len(self.proxies), max_retries * 2)) 
        
        attempts = 0
        for proxy in candidates:
            if attempts >= max_retries:
                break
                
            if self.check_proxy(proxy):
                # Double check: remove from strict rotation? 
                # For now we keep it in the pool but randomness handles rotation.
                log.info(f"🚀 Selected proxy: {proxy}")
                return proxy
            
            attempts += 1
            
        log.warning("❌ All proxy attempts failed. Falling back to local IP.")
        return None

# Singleton instance
proxy_manager = ProxyManager()
