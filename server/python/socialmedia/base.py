import json
import os
import base64
from typing import Optional, Literal, Any, Dict

class BaseScrape:
    """Base class for social media scrapers."""
    
    def __init__(self):
        self.raw_data: Optional[Dict[str, Any]] = None
    
    def _type(self, type: Literal['raw', 'clean', 'bs64'] = 'raw'):
        """Convert data to specified type."""
        if type == 'raw':
            return self.raw_data
        elif type == 'clean':
            return self._clean(self.raw_data)
        elif type == 'bs64':
            return base64.b64encode(
                json.dumps(self.raw_data).encode()
            ).decode()
        return None
    
    def _clean(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean raw data. To be implemented by child classes."""
        raise NotImplementedError
    
    def _save(self, directory: str):
        """Save data to file."""
        if not self.raw_data:
            return
            
        os.makedirs(directory, exist_ok=True)
        filename = os.path.join(directory, f"data_{self.__class__.__name__}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.raw_data, f, indent=2, ensure_ascii=False) 