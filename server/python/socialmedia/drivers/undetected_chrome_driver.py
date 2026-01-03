"""
Undetected Chrome Driver
Uses undetected-chromedriver for stealthy browser automation.
This driver evades most anti-bot detection systems.
"""

import logging
import platform
import random
from typing import List, Any, Dict, Optional
from .base_scraper import BaseScraper

log = logging.getLogger(__name__)


class UndetectedChromeDriver(BaseScraper):
    """
    Scraper driver using undetected-chromedriver.
    Automatically patches Chrome to evade bot detection.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self._is_setup = False
        self._virtual_display = None
    
    def setup(self, proxy: Optional[str] = None) -> None:
        """Initialize undetected-chromedriver."""
        try:
            import undetected_chromedriver as uc
            from selenium.webdriver.chrome.options import Options
            
            log.info(f"Initializing undetected-chromedriver... (Proxy: {proxy if proxy else 'None'})")
            
            # Detect OS and set up virtual display for Linux servers
            is_linux = platform.system() == "Linux"
            
            if is_linux and self.headless:
                # Use xvfb virtual display on Linux
                try:
                    from pyvirtualdisplay import Display
                    log.info("Linux detected. Starting xvfb virtual display...")
                    self._virtual_display = Display(visible=False, size=(1920, 1080))
                    self._virtual_display.start()
                    log.info("Virtual display started successfully")
                except ImportError:
                    log.warning("pyvirtualdisplay not available")
                except Exception as e:
                    log.warning(f"Failed to start virtual display: {e}")
            
            # Configure Chrome options
            options = uc.ChromeOptions()
            
            # Randomize viewport
            viewports = [
                (1920, 1080),
                (1536, 864),
                (1440, 900),
                (1366, 768),
                (1280, 720),
            ]
            width, height = random.choice(viewports)
            options.add_argument(f"--window-size={width},{height}")
            
            # Common stealth options
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--lang=en-US,en")
            
            # User agent randomization
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ]
            options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            # Proxy configuration
            if proxy:
                # Parse proxy URL to handle authentication
                if "@" in proxy:
                    # Proxy with auth: http://user:pass@host:port
                    # undetected-chromedriver handles this via extension
                    log.info(f"Configuring authenticated proxy...")
                    options.add_argument(f"--proxy-server={proxy}")
                else:
                    # Simple proxy: http://host:port
                    options.add_argument(f"--proxy-server={proxy}")
            
            # Headless mode
            # Note: True headless is more detectable, so we use virtual display on Linux instead
            if self.headless and not is_linux:
                # On Windows/Mac with headless, use the headless option
                options.add_argument("--headless=new")
            
            # Create the undetected Chrome driver
            self.driver = uc.Chrome(
                options=options,
                use_subprocess=True,
                version_main=None,  # Auto-detect Chrome version
            )
            
            # Set timeouts
            self.driver.set_page_load_timeout(60)
            self.driver.implicitly_wait(10)
            
            # Apply additional fingerprint obfuscation
            self._apply_fingerprint_obfuscation()
            
            self._is_setup = True
            log.info(f"Undetected Chrome driver initialized (viewport: {width}x{height})")
            
        except Exception as e:
            log.error(f"Failed to initialize undetected-chromedriver: {e}")
            self._cleanup()
            raise
    
    def _apply_fingerprint_obfuscation(self):
        """Apply JavaScript to further obfuscate browser fingerprint."""
        try:
            fingerprint_script = """
                // Additional webdriver detection override
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override Chrome automation flags
                window.chrome = window.chrome || {};
                window.chrome.runtime = window.chrome.runtime || {};
                
                // Plugins array
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                console.log('Fingerprint obfuscation applied');
            """
            self.driver.execute_script(fingerprint_script)
            log.info("Fingerprint obfuscation applied")
        except Exception as e:
            log.warning(f"Failed to apply fingerprint obfuscation: {e}")
    
    def _cleanup(self):
        """Internal cleanup helper."""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
        try:
            if self._virtual_display:
                self._virtual_display.stop()
                log.info("Virtual display stopped")
        except:
            pass
        self.driver = None
        self._virtual_display = None
        self._is_setup = False
    
    def get(self, url: str, timeout: int = 30) -> None:
        """Navigate to a URL."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        self.driver.get(url)
    
    def find_element(self, by: str, value: str) -> Any:
        """Find a single element."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        return self.driver.find_element(by, value)
    
    def find_elements(self, by: str, value: str) -> List[Any]:
        """Find multiple elements."""
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
        self.driver.add_cookie(cookie)
    
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
    
    def set_window_size(self, width: int, height: int) -> None:
        """Set window size."""
        if not self._is_setup:
            raise RuntimeError("Driver not setup. Call setup() first.")
        self.driver.set_window_size(width, height)
    
    def is_bot_detected(self) -> bool:
        """Check if bot detection has been triggered."""
        if not self._is_setup:
            return False
        try:
            content = self.page_source.lower()
            url = self.current_url.lower()
            
            # More specific bot indicators to avoid false positives
            # Avoid single words like 'challenge' which appear in normal TikTok content
            bot_indicators = [
                'captcha',
                'are you a robot',
                'verify you are human',
                'access denied',
                'unusual traffic',
                'security check',
                'please verify',
                'bot detection',
                'automated access',
            ]
            
            # Check URL for specific bot-related paths
            url_indicators = [
                '/challenge',  # Verification challenge, not hashtag challenge
                '/verify',
                '/captcha',
            ]
            
            content_detected = any(indicator in content for indicator in bot_indicators)
            url_detected = any(indicator in url for indicator in url_indicators)
            
            return content_detected or url_detected
        except:
            return False
    
    def sleep(self, seconds: float) -> None:
        """Human-like sleep."""
        import time
        # Add slight randomness for more human-like behavior
        jitter = random.uniform(0, seconds * 0.1)
        time.sleep(seconds + jitter)
    
    def quit(self) -> None:
        """Clean up and close the driver."""
        self._cleanup()
        log.info("Undetected Chrome driver closed")
