from abc import ABC, abstractmethod
from typing import List

from app.models import Listing


class Source(ABC):
    """Abstract base class for price comparison sources."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the source name (e.g., 'eBay', 'Google Shopping')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this source is available (e.g., API key configured)."""
        pass

    @abstractmethod
    async def search(self, query: str) -> List[Listing]:
        """
        Search for products matching the query.

        Args:
            query: Search query string

        Returns:
            List of Listing objects found
        """
        pass
