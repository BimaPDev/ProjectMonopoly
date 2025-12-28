"""
Base Scraper Interface
Abstract base class defining the common interface for all scraper drivers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict


class BaseScraper(ABC):
    """Abstract base class for web scraper drivers."""
    
    @abstractmethod
    def setup(self) -> None:
        """Initialize the driver."""
        pass
    
    @abstractmethod
    def get(self, url: str) -> None:
        """Navigate to a URL."""
        pass
    
    @abstractmethod
    def find_element(self, by: str, value: str) -> Any:
        """Find a single element."""
        pass
    
    @abstractmethod
    def find_elements(self, by: str, value: str) -> List[Any]:
        """Find multiple elements."""
        pass
    
    @property
    @abstractmethod
    def page_source(self) -> str:
        """Get the current page HTML."""
        pass
    
    @property
    @abstractmethod
    def current_url(self) -> str:
        """Get the current URL."""
        pass
    
    @property
    @abstractmethod
    def title(self) -> str:
        """Get the current page title."""
        pass
    
    @abstractmethod
    def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript in the browser."""
        pass
    
    @abstractmethod
    def get_cookies(self) -> List[Dict]:
        """Get all cookies."""
        pass
    
    @abstractmethod
    def add_cookie(self, cookie: Dict) -> None:
        """Add a cookie."""
        pass
    
    @abstractmethod
    def save_screenshot(self, filename: str) -> None:
        """Save a screenshot."""
        pass
    
    @abstractmethod
    def set_page_load_timeout(self, timeout: int) -> None:
        """Set page load timeout in seconds."""
        pass
    
    @abstractmethod
    def quit(self) -> None:
        """Clean up and close the driver."""
        pass
    
    def is_bot_detected(self) -> bool:
        """
        Check if bot detection has been triggered.
        Override in subclasses for specific detection logic.
        """
        try:
            source = self.page_source.lower()
            url = self.current_url.lower()
            
            # Common bot detection indicators
            bot_indicators = [
                'captcha',
                'challenge',
                'verify you are human',
                'unusual traffic',
                'automated access',
                'rate limit',
                'too many requests',
                'blocked',
                'access denied',
            ]
            
            for indicator in bot_indicators:
                if indicator in source or indicator in url:
                    return True
            
            return False
        except Exception:
            return False
