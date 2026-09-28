from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseDocumentParser(ABC):
    """
    Abstract interface for document-specific OCR output parsing.
    """
    @abstractmethod
    def parse(self, raw_text: str) -> Dict[str, Any]:
        """
        Parses raw OCR text and returns structured fields:
        {
            "masked_id": Optional[str],
            "fields": Dict[str, Any],
            "raw_text_summary": str
        }
        """
        pass
