"""
SeleniumBase Driver
Primary scraper driver using SeleniumBase with UC (Undetected ChromeDriver) mode.
"""

import logging
from typing import List, Any, Dict, Optional
from .base_scraper import BaseScraper

log = logging.getLogger(__name__)


class SeleniumBaseDriver(BaseScraper):
    """
    Primary scraper driver using SeleniumBase with UC mode.
    Provides better anti-detection than standard Selenium or undetected-chromedriver.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.sb = None
        self.driver = None
        self._is_setup = False
    
    def setup(self) -> None:
        """Initialize SeleniumBase driver with UC mode."""
        try:
            from seleniumbase import SB
            
            log.info("Initializing SeleniumBase with UC mode...")
            
            # Create SB instance with UC mode enabled
            self.sb = SB(
                uc=True,  # Undetected ChromeDriver mode
                headless=self.headless,
                headed=not self.headless,
                # Additional anti-detection options
                uc_cdp=True,  # Use CDP for UC mode
            )
            
            # Enter the context manager to start the browser
            self.sb.__enter__()
            self.driver = self.sb.driver
            self._is_setup = True
            
            log.info("SeleniumBase driver initialized successfully")
            
        except Exception as e:
            log.error(f"Failed to initialize SeleniumBase: {e}")
            raise
    
    def get(self, url: str) -> None:
        """Navigate to a URL."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        self.sb.open(url)
    
    def find_element(self, by: str, value: str) -> Any:
        """Find a single element using Selenium locators."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.driver.find_element(by, value)
    
    def find_elements(self, by: str, value: str) -> List[Any]:
        """Find multiple elements using Selenium locators."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.driver.find_elements(by, value)
    
    @property
    def page_source(self) -> str:
        """Get the current page HTML."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.driver.page_source
    
    @property
    def current_url(self) -> str:
        """Get the current URL."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.driver.current_url
    
    @property
    def title(self) -> str:
        """Get the current page title."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.driver.title
    
    def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript in the browser."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.driver.execute_script(script, *args)
    
    def get_cookies(self) -> List[Dict]:
        """Get all cookies."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.driver.get_cookies()
    
    def add_cookie(self, cookie: Dict) -> None:
        """Add a cookie."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        # Remove problematic cookie attributes
        cookie_copy = cookie.copy()
        cookie_copy.pop('sameSite', None)
        self.driver.add_cookie(cookie_copy)
    
    def save_screenshot(self, filename: str) -> None:
        """Save a screenshot."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        self.driver.save_screenshot(filename)
    
    def set_page_load_timeout(self, timeout: int) -> None:
        """Set page load timeout in seconds."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        self.driver.set_page_load_timeout(timeout)
    
    def wait_for_element(self, selector: str, timeout: int = 10) -> Any:
        """SeleniumBase native wait for element."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.sb.wait_for_element(selector, timeout=timeout)
    
    def click(self, selector: str) -> None:
        """SeleniumBase native click with anti-detection."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        self.sb.click(selector)
    
    def type(self, selector: str, text: str) -> None:
        """SeleniumBase native type with human-like delays."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        self.sb.type(selector, text)
    
    def quit(self) -> None:
        """Clean up and close the driver."""
        if self.sb and self._is_setup:
            try:
                self.sb.__exit__(None, None, None)
            except Exception as e:
                log.warning(f"Error during driver cleanup: {e}")
            finally:
                self.sb = None
                self.driver = None
                self._is_setup = False
                log.info("SeleniumBase driver closed")
