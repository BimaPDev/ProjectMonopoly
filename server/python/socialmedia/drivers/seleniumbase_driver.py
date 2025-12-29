"""
SeleniumBase CDP Driver with Playwright
Uses SeleniumBase's sb_cdp mode connected to Playwright for stealthy scraping.
This approach doesn't require chromedriver and is more reliable for anti-bot sites.
"""

import logging
import platform
from typing import List, Any, Dict, Optional
from .base_scraper import BaseScraper

log = logging.getLogger(__name__)


class SeleniumBaseDriver(BaseScraper):
    """
    Scraper driver using SeleniumBase's sb_cdp mode with Playwright connection.
    Uses CDP (Chrome DevTools Protocol) for better stealth capabilities.
    
    On Linux servers without a display (Docker), uses xvfb virtual display.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.sb = None
        self.page = None
        self.browser = None
        self.playwright = None
        self.context = None
        self._is_setup = False
        self._virtual_display = None  # For xvfb on Linux
    
    def setup(self) -> None:
        """Initialize SeleniumBase with CDP mode connected to Playwright."""
        try:
            from seleniumbase import sb_cdp
            from playwright.sync_api import sync_playwright
            
            log.info("Initializing SeleniumBase CDP mode with Playwright...")
            
            # Detect OS and set up virtual display for Linux servers
            is_linux = platform.system() == "Linux"
            
            if is_linux and self.headless:
                # On Linux with headless mode, use xvfb virtual display
                # This tricks TikTok into thinking there's a real display
                try:
                    from pyvirtualdisplay import Display
                    print("Linux detected. Starting xvfb virtual display...")
                    self._virtual_display = Display(visible=False, size=(1920, 1080))
                    self._virtual_display.start()
                    print("Virtual display started successfully")
                except ImportError:
                    print("pyvirtualdisplay not available. Using headless=False")
                except Exception as e:
                    print(f"Failed to start virtual display: {e}")
            
            # Create sb_cdp Chrome instance (no WebDriver needed)
            # NOTE: TikTok blocks true headless Chrome, always use visible mode
            # On Linux with xvfb, the "visible" browser renders to the virtual display
            print("Starting Chrome browser (visible mode - required for TikTok)")
            self.sb = sb_cdp.Chrome(headless=False)
            
            endpoint_url = self.sb.get_endpoint_url()
            log.info(f"SeleniumBase CDP endpoint: {endpoint_url}")
            
            # Connect Playwright to the CDP endpoint
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp(endpoint_url)
            self.context = self.browser.contexts[0]
            self.page = self.context.pages[0]
            
            # Set viewport to look like a real desktop browser
            self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            self._is_setup = True
            log.info("SeleniumBase CDP + Playwright driver initialized successfully")
            
        except Exception as e:
            log.error(f"Failed to initialize SeleniumBase CDP driver: {e}")
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
            if self.browser:
                self.browser.close()
        except:
            pass
        try:
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        try:
            if self.sb:
                self.sb.quit()
        except:
            pass
        # Stop virtual display if running (Linux xvfb)
        try:
            if self._virtual_display:
                self._virtual_display.stop()
                print("Virtual display stopped")
        except:
            pass
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        self.sb = None
        self._virtual_display = None
        self._is_setup = False
    
    def get(self, url: str) -> None:
        """Navigate to a URL."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        self.page.goto(url, wait_until='domcontentloaded')
    
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
    
    # Provide a driver-like property for compatibility with existing code
    @property
    def driver(self):
        """Return self for compatibility - use page for operations."""
        return self
    
    def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript in the browser. Handles Selenium-style scripts."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        
        # Convert Selenium-style "return X" to Playwright's evaluate format
        # Playwright expects an expression or arrow function, not bare return
        if script.strip().startswith("return "):
            # Wrap in arrow function: "return X" -> "() => X"
            expression = script.strip()[7:]  # Remove "return "
            script = f"() => {expression}"
        
        return self.page.evaluate(script, *args) if args else self.page.evaluate(script)
    
    def get_cookies(self) -> List[Dict]:
        """Get all cookies."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        cookies = self.context.cookies()
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
        pw_cookie = {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie.get('domain', ''),
            'path': cookie.get('path', '/'),
            'secure': cookie.get('secure', False),
            'httpOnly': cookie.get('httpOnly', False),
        }
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
    
    def set_window_size(self, width: int, height: int) -> None:
        """Set viewport size."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        self.page.set_viewport_size({"width": width, "height": height})
    
    def wait_for_selector(self, selector: str, timeout: int = 10000) -> Any:
        """Wait for a selector to appear."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.page.wait_for_selector(selector, timeout=timeout)
    
    def is_bot_detected(self) -> bool:
        """Check if bot detection has been triggered."""
        if not self._is_setup:
            return False
        try:
            # Check for common bot detection indicators
            content = self.page.content().lower()
            bot_indicators = [
                'captcha',
                'are you a robot',
                'verify you are human',
                'access denied',
                'blocked',
                'unusual traffic',
            ]
            return any(indicator in content for indicator in bot_indicators)
        except:
            return False
    
    def quit(self) -> None:
        """Clean up and close the driver."""
        self._cleanup()
        log.info("SeleniumBase CDP driver closed")
