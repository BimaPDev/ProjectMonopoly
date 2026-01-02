"""
Playwright Stealth Driver
Fallback scraper driver using Playwright with stealth plugin.
Used when SeleniumBase triggers bot detection.
"""

import logging
from typing import List, Any, Dict, Optional
from .base_scraper import BaseScraper

log = logging.getLogger(__name__)


class PlaywrightStealthDriver(BaseScraper):
    """
    Fallback scraper driver using Playwright with stealth mode.
    Provides a different browser fingerprint when Selenium-based drivers are detected.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._is_setup = False
    
    def setup(self, proxy: Optional[str] = None) -> None:
        """Initialize Playwright with stealth mode."""
        try:
            from playwright.sync_api import sync_playwright
            
            log.info(f"Initializing Playwright with stealth mode... (Proxy: {proxy if proxy else 'None'})")
            
            self.playwright = sync_playwright().start()
            
            launch_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-size=1920,1080',
                '--disable-extensions',
            ]
            
            # Convert proxy string to Playwright dictionary format if present
            # Format: 'protocol://server:port'
            pw_proxy = None
            if proxy:
               if '://' in proxy:
                   scheme, rest = proxy.split('://', 1)
                   server = rest
               else:
                   scheme = 'http'
                   server = proxy
                   
               # Playwright expects {server: "ip:port"} or {server: "scheme://ip:port"}
               # It handles socks5:// prefix natively
               pw_proxy = {"server": f"{scheme}://{server}"}

            # Launch Chromium with stealth-friendly options
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                proxy=pw_proxy,
                args=launch_args
            )
            
            # Create context with realistic viewport and user agent
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
            )
            
            self.page = self.context.new_page()
            
            # Apply stealth mode - handle both old and new API versions
            # Apply stealth mode - verified API for v2.0+
            try:
                from playwright_stealth import Stealth
                stealth = Stealth()
                # Based on dir() inspection: apply_stealth_sync is the method
                stealth.apply_stealth_sync(self.page)
                log.info("Applied stealth using verified API (Stealth().apply_stealth_sync())")
            except Exception as e:
                log.warning(f"playwright_stealth failed to apply: {e}")


            
            self._is_setup = True
            log.info("Playwright stealth driver initialized successfully")
            
        except Exception as e:
            log.error(f"Failed to initialize Playwright: {e}")
            self._cleanup()
            raise
    
    def _cleanup(self):
        """Internal cleanup helper."""
        try:
            if self.page:
                self.page.close()
        except:
            pass
        try:
            if self.context:
                self.context.close()
        except:
            pass
        try:
            if self.browser:
                self.browser.close()
        except:
            pass
        try:
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        self._is_setup = False
    
    def get(self, url: str, timeout: int = 30000) -> None:
        """Navigate to a URL with timeout protection.
        
        Args:
            url: The URL to navigate to
            timeout: Maximum time in milliseconds to wait (default 30 seconds)
        """
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        try:
            self.page.goto(url, wait_until='commit', timeout=timeout)
        except Exception as e:
            log.warning(f"Navigation timeout/error for {url}: {e}")
    
    def find_element(self, by: str, value: str) -> Any:
        """Find a single element. Converts Selenium locators to Playwright."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        selector = self._convert_locator(by, value)
        return self.page.locator(selector).first
    
    def find_elements(self, by: str, value: str) -> List[Any]:
        """Find multiple elements. Converts Selenium locators to Playwright."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        selector = self._convert_locator(by, value)
        return self.page.locator(selector).all()
    
    def _convert_locator(self, by: str, value: str) -> str:
        """Convert Selenium By locators to Playwright selectors."""
        # Import Selenium By for comparison
        from selenium.webdriver.common.by import By
        
        if by == By.ID:
            return f'#{value}'
        elif by == By.CLASS_NAME:
            return f'.{value}'
        elif by == By.NAME:
            return f'[name="{value}"]'
        elif by == By.TAG_NAME:
            return value
        elif by == By.XPATH:
            return f'xpath={value}'
        elif by == By.CSS_SELECTOR:
            return value
        elif by == By.LINK_TEXT:
            return f'text="{value}"'
        elif by == By.PARTIAL_LINK_TEXT:
            return f'text={value}'
        else:
            # Assume it's already a valid selector
            return value
    
    @property
    def page_source(self) -> str:
        """Get the current page HTML."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.page.content()
    
    @property
    def current_url(self) -> str:
        """Get the current URL."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.page.url
    
    @property
    def title(self) -> str:
        """Get the current page title."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.page.title()
    
    def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript in the browser. Handles Selenium-style scripts."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        
        # Convert Selenium-style "return X" to Playwright's evaluate format
        if script.strip().startswith("return "):
            expression = script.strip()[7:]
            script = f"() => {expression}"
        
        return self.page.evaluate(script, *args) if args else self.page.evaluate(script)
    
    def get_cookies(self) -> List[Dict]:
        """Get all cookies."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        cookies = self.context.cookies()
        # Convert Playwright cookie format to Selenium-like format
        return [
            {
                'name': c['name'],
                'value': c['value'],
                'domain': c.get('domain', ''),
                'path': c.get('path', '/'),
                'secure': c.get('secure', False),
                'httpOnly': c.get('httpOnly', False),
            }
            for c in cookies
        ]
    
    def add_cookie(self, cookie: Dict) -> None:
        """Add a cookie."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        # Convert Selenium cookie format to Playwright format
        pw_cookie = {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie.get('domain', ''),
            'path': cookie.get('path', '/'),
            'secure': cookie.get('secure', False),
            'httpOnly': cookie.get('httpOnly', False),
        }
        # Remove empty domain (Playwright requires it to be set or omitted)
        if not pw_cookie['domain']:
            pw_cookie.pop('domain')
        self.context.add_cookies([pw_cookie])
    
    def save_screenshot(self, filename: str) -> None:
        """Save a screenshot."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        self.page.screenshot(path=filename)
    
    def set_page_load_timeout(self, timeout: int) -> None:
        """Set page load timeout in seconds."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        self.page.set_default_timeout(timeout * 1000)  # Playwright uses ms
    
    def wait_for_selector(self, selector: str, timeout: int = 10000) -> Any:
        """Wait for a selector to appear."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.page.wait_for_selector(selector, timeout=timeout)
    
    def quit(self) -> None:
        """Clean up and close the driver."""
        self._cleanup()
        log.info("Playwright stealth driver closed")
