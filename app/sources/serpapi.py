import re
from typing import List, Optional

import httpx

from app.models import Listing
from app.sources.base import Source
from config import settings


class SerpApiSource(Source):
    """Google Shopping via SerpAPI integration."""

    API_URL = "https://serpapi.com/search"

    @property
    def name(self) -> str:
        return "Google Shopping"

    def is_available(self) -> bool:
        return settings.serpapi_available

    async def search(self, query: str) -> List[Listing]:
        if not self.is_available():
            return []

        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": settings.SERPAPI_KEY,
            "num": "20",
            "gl": "us",  # Country
            "hl": "en",  # Language
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.API_URL, params=params)
                response.raise_for_status()
                data = response.json()

            return self._parse_response(data)

        except Exception:
            # Graceful degradation - return empty on error
            return []

    def _parse_response(self, data: dict) -> List[Listing]:
        listings = []

        shopping_results = data.get("shopping_results", [])

        for result in shopping_results:
            listing = self._parse_result(result)
            if listing:
                listings.append(listing)

        return listings

    def _parse_result(self, result: dict) -> Optional[Listing]:
        try:
            # Extract price - prefer extracted_price (numeric) over price (string)
            price = result.get("extracted_price")
            if price is None:
                price_str = result.get("price", "")
                price = self._extract_price(price_str)

            if price is None or price <= 0:
                return None

            # Extract shipping from delivery info or assume free
            shipping = 0.0
            delivery = result.get("delivery", "")
            if delivery:
                shipping = self._extract_shipping(delivery)

            # Condition - Google Shopping typically shows new items
            # but we can infer from title/snippet
            title = result.get("title", "").lower()
            condition = self._infer_condition(title)

            # Extract URL
            url = result.get("product_link", "")
            if not url:
                return None

            return Listing.create(
                source=f"{self.name} ({result.get('source', 'Unknown')})",
                price=float(price),
                shipping=shipping,
                condition=condition,
                url=url,
            )

        except (KeyError, ValueError):
            return None

    def _extract_price(self, price_str: str) -> Optional[float]:
        """Extract numeric price from string like '$299.99'."""
        if not price_str:
            return None

        # Remove currency symbols and commas
        cleaned = re.sub(r"[^\d.]", "", price_str)
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _extract_shipping(self, delivery_str: str) -> float:
        """Extract shipping cost from delivery string."""
        delivery_lower = delivery_str.lower()

        if "free" in delivery_lower:
            return 0.0

        # Try to find a price in the delivery string
        match = re.search(r"\$?([\d.]+)", delivery_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        return 0.0

    def _infer_condition(self, title: str) -> str:
        """Infer condition from title keywords."""
        title_lower = title.lower()

        if any(word in title_lower for word in ["refurbished", "renewed", "certified"]):
            return "refurbished"
        if any(word in title_lower for word in ["used", "pre-owned", "preowned"]):
            return "used"
        if any(word in title_lower for word in ["open box", "open-box"]):
            return "used"

        # Default to new for Google Shopping results
        return "new"
