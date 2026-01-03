"""
Driver Factory
Smart factory that supports multiple driver types with automatic fallback.
Drivers: Undetected Chrome, SeleniumBase, Playwright
"""

import logging
from typing import Tuple, Optional, Union
from .seleniumbase_driver import SeleniumBaseDriver
from .playwright_stealth_driver import PlaywrightStealthDriver
from .undetected_chrome_driver import UndetectedChromeDriver
from .base_scraper import BaseScraper

log = logging.getLogger(__name__)


class BotDetectedError(Exception):
    """Raised when bot detection is triggered."""
    pass


class DriverFactory:
    """
    Factory for creating scraper drivers with automatic fallback.
    
    Driver priority:
    1. Undetected Chrome (if force_undetected=True)
    2. SeleniumBase (default primary)
    3. Playwright (fallback)
    """
    
    @staticmethod
    def create(
        headless: bool = True,
        force_playwright: bool = False,
        force_undetected: bool = False,
        skip_seleniumbase: bool = False,
        proxy: Optional[str] = None,
    ) -> Tuple[BaseScraper, str]:
        """
        Create a scraper driver.
        
        Args:
            headless: Run browser in headless mode
            force_playwright: Skip other drivers and use Playwright directly
            force_undetected: Use undetected-chromedriver (best for anti-bot sites)
            skip_seleniumbase: Same as force_playwright (alias)
            proxy: Optional proxy string (e.g. "http://1.2.3.4:8080")
        
        Returns:
            Tuple of (driver instance, driver type string)
        """
        # If undetected browser is requested, try it first
        if force_undetected:
            try:
                log.info("Attempting to initialize Undetected Chrome driver...")
                driver = UndetectedChromeDriver(headless=headless)
                driver.setup(proxy=proxy)
                log.info("Undetected Chrome driver ready")
                return driver, 'undetected'
            except Exception as e:
                log.warning(f"Undetected Chrome failed: {e}")
                log.info("Falling back to SeleniumBase...")
        
        use_playwright = force_playwright or skip_seleniumbase
        
        if not use_playwright:
            try:
                log.info("Attempting to initialize SeleniumBase driver...")
                driver = SeleniumBaseDriver(headless=headless)
                driver.setup(proxy=proxy)
                log.info("SeleniumBase driver ready")
                return driver, 'seleniumbase'
            except Exception as e:
                log.warning(f"SeleniumBase failed: {e}")
                log.info("Falling back to Playwright...")
        
        # Fallback to Playwright
        try:
            log.info("Initializing Playwright stealth driver...")
            driver = PlaywrightStealthDriver(headless=headless)
            driver.setup(proxy=proxy)
            log.info("Playwright stealth driver ready")
            return driver, 'playwright'
        except Exception as e:
            log.error(f"Playwright also failed: {e}")
            raise RuntimeError("Failed to initialize any scraper driver") from e


def get_driver(
    headless: bool = True,
    force_playwright: bool = False,
    force_undetected: bool = False,
    proxy: Optional[str] = None,
) -> Tuple[BaseScraper, str]:
    """
    Convenience function to get a scraper driver.
    
    Args:
        headless: Run browser in headless mode
        force_playwright: Skip other drivers and use Playwright directly
        force_undetected: Use undetected-chromedriver (best for anti-bot sites)
        proxy: Optional proxy string
    
    Returns:
        Tuple of (driver instance, driver type string)
    """
    return DriverFactory.create(
        headless=headless, 
        force_playwright=force_playwright, 
        force_undetected=force_undetected,
        proxy=proxy
    )


def switch_to_fallback(
    current_driver: BaseScraper, 
    headless: bool = True,
    proxy: Optional[str] = None
) -> Tuple[BaseScraper, str]:
    """
    Switch from current driver to fallback (Playwright).
    Useful when bot detection is triggered mid-scrape.
    
    Args:
        current_driver: The current driver to close
        headless: Run new browser in headless mode
        proxy: Optional proxy to use for fallback
    
    Returns:
        Tuple of (new driver instance, driver type string)
    """
    log.info("Switching to fallback driver due to bot detection...")
    
    try:
        current_driver.quit()
    except Exception as e:
        log.warning(f"Error closing current driver: {e}")
    
    return get_driver(headless=headless, force_playwright=True, proxy=proxy)
