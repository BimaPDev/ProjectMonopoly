"""
Driver Factory
Smart factory that tries SeleniumBase first, automatically falls back to Playwright on bot detection.
"""

import logging
from typing import Tuple, Optional, Union
from .seleniumbase_driver import SeleniumBaseDriver
from .playwright_stealth_driver import PlaywrightStealthDriver
from .base_scraper import BaseScraper

log = logging.getLogger(__name__)


class BotDetectedError(Exception):
    """Raised when bot detection is triggered."""
    pass


class DriverFactory:
    """
    Factory for creating scraper drivers with automatic fallback.
    Tries SeleniumBase first, falls back to Playwright if bot detection occurs.
    """
    
    @staticmethod
    def create(
        headless: bool = True,
        force_playwright: bool = False,
        skip_seleniumbase: bool = False,
    ) -> Tuple[BaseScraper, str]:
        """
        Create a scraper driver.
        
        Args:
            headless: Run browser in headless mode
            force_playwright: Skip SeleniumBase and use Playwright directly
            skip_seleniumbase: Same as force_playwright (alias)
        
        Returns:
            Tuple of (driver instance, driver type string)
        """
        use_playwright = force_playwright or skip_seleniumbase
        
        if not use_playwright:
            try:
                log.info("Attempting to initialize SeleniumBase driver...")
                driver = SeleniumBaseDriver(headless=headless)
                driver.setup()
                log.info("SeleniumBase driver ready")
                return driver, 'seleniumbase'
            except Exception as e:
                log.warning(f"SeleniumBase failed: {e}")
                log.info("Falling back to Playwright...")
        
        # Fallback to Playwright
        try:
            log.info("Initializing Playwright stealth driver...")
            driver = PlaywrightStealthDriver(headless=headless)
            driver.setup()
            log.info("Playwright stealth driver ready")
            return driver, 'playwright'
        except Exception as e:
            log.error(f"Playwright also failed: {e}")
            raise RuntimeError("Failed to initialize any scraper driver") from e


def get_driver(
    headless: bool = True,
    force_playwright: bool = False,
) -> Tuple[BaseScraper, str]:
    """
    Convenience function to get a scraper driver.
    
    Args:
        headless: Run browser in headless mode
        force_playwright: Skip SeleniumBase and use Playwright directly
    
    Returns:
        Tuple of (driver instance, driver type string)
    """
    return DriverFactory.create(headless=headless, force_playwright=force_playwright)


def switch_to_fallback(current_driver: BaseScraper, headless: bool = True) -> Tuple[BaseScraper, str]:
    """
    Switch from current driver to fallback (Playwright).
    Useful when bot detection is triggered mid-scrape.
    
    Args:
        current_driver: The current driver to close
        headless: Run new browser in headless mode
    
    Returns:
        Tuple of (new driver instance, driver type string)
    """
    log.info("Switching to fallback driver due to bot detection...")
    
    try:
        current_driver.quit()
    except Exception as e:
        log.warning(f"Error closing current driver: {e}")
    
    return get_driver(headless=headless, force_playwright=True)
