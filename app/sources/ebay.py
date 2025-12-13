from typing import List, Optional

import httpx

from app.models import Listing
from app.sources.base import Source
from config import settings


# eBay condition ID to human-readable mapping
CONDITION_MAP = {
    "1000": "new",
    "1500": "new",  # New other
    "1750": "new",  # New with defects
    "2000": "refurbished",  # Certified refurbished
    "2010": "refurbished",  # Excellent - Refurbished
    "2020": "refurbished",  # Very Good - Refurbished
    "2030": "refurbished",  # Good - Refurbished
    "2500": "refurbished",  # Seller refurbished
    "2750": "used",  # Like New
    "3000": "used",
    "4000": "used",  # Very Good
    "5000": "used",  # Good
    "6000": "used",  # Acceptable
    "7000": "used",  # For parts
}


class EbaySource(Source):
    """eBay Finding API integration."""

    FINDING_API_URL = "https://svcs.ebay.com/services/search/FindingService/v1"

    @property
    def name(self) -> str:
        return "eBay"

    def is_available(self) -> bool:
        return settings.ebay_available

    async def search(self, query: str) -> List[Listing]:
        if not self.is_available():
            return []

        params = {
            "OPERATION-NAME": "findItemsByKeywords",
            "SERVICE-VERSION": "1.0.0",
            "SECURITY-APPNAME": settings.EBAY_APP_ID,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "keywords": query,
            "paginationInput.entriesPerPage": "20",
            "sortOrder": "PricePlusShippingLowest",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.FINDING_API_URL, params=params)
                response.raise_for_status()
                data = response.json()

            return self._parse_response(data)

        except Exception:
            # Graceful degradation - return empty on error
            return []

    def _parse_response(self, data: dict) -> List[Listing]:
        listings = []

        try:
            search_result = (
                data.get("findItemsByKeywordsResponse", [{}])[0]
                .get("searchResult", [{}])[0]
            )

            items = search_result.get("item", [])

            for item in items:
                listing = self._parse_item(item)
                if listing:
                    listings.append(listing)

        except (KeyError, IndexError):
            pass

        return listings

    def _parse_item(self, item: dict) -> Optional[Listing]:
        try:
            # Extract price
            selling_status = item.get("sellingStatus", [{}])[0]
            current_price = selling_status.get("currentPrice", [{}])[0]
            price = float(current_price.get("__value__", 0))

            # Extract shipping cost
            shipping_info = item.get("shippingInfo", [{}])[0]
            shipping_cost = shipping_info.get("shippingServiceCost", [{}])
            if shipping_cost:
                shipping = float(shipping_cost[0].get("__value__", 0))
            else:
                # Free shipping or not specified
                shipping_type = shipping_info.get("shippingType", [""])[0]
                shipping = 0.0 if shipping_type == "Free" else 0.0

            # Extract condition
            condition_info = item.get("condition", [{}])[0]
            condition_id = condition_info.get("conditionId", [""])[0]
            condition = CONDITION_MAP.get(condition_id, "unknown")

            # Extract URL
            url = item.get("viewItemURL", [""])[0]

            if not url or price <= 0:
                return None

            return Listing.create(
                source=self.name,
                price=price,
                shipping=shipping,
                condition=condition,
                url=url,
            )

        except (KeyError, IndexError, ValueError):
            return None
