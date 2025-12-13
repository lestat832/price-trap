import hashlib
import random
from typing import List

from app.models import Listing
from app.sources.base import Source
from config import settings


class MockSource(Source):
    """Mock source for testing without API keys."""

    # Simulated marketplaces
    MOCK_SOURCES = [
        ("eBay", "https://www.ebay.com/itm/"),
        ("Amazon", "https://www.amazon.com/dp/"),
        ("Best Buy", "https://www.bestbuy.com/site/"),
        ("Walmart", "https://www.walmart.com/ip/"),
        ("Target", "https://www.target.com/p/"),
        ("B&H Photo", "https://www.bhphotovideo.com/c/product/"),
        ("Newegg", "https://www.newegg.com/p/"),
    ]

    CONDITIONS = ["new", "new", "new", "used", "used", "refurbished"]

    @property
    def name(self) -> str:
        return "Mock"

    def is_available(self) -> bool:
        # Available when mock mode is enabled OR when no real sources are configured
        return settings.MOCK_MODE or not settings.any_real_source_available

    async def search(self, query: str) -> List[Listing]:
        if not self.is_available():
            return []

        # Use query hash as seed for reproducible results
        seed = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        # Generate 6-8 mock listings
        num_listings = rng.randint(6, 8)
        listings = []

        # Base price varies by query length (just for variety)
        base_price = 100 + (len(query) * 10) + rng.uniform(-20, 50)

        for i in range(num_listings):
            source_name, base_url = rng.choice(self.MOCK_SOURCES)

            # Price varies around base
            price_multiplier = rng.uniform(0.7, 1.5)
            price = round(base_price * price_multiplier, 2)

            # Shipping: 0-15, with 40% chance of free shipping
            if rng.random() < 0.4:
                shipping = 0.0
            else:
                shipping = round(rng.uniform(3.99, 14.99), 2)

            condition = rng.choice(self.CONDITIONS)

            # Used/refurb items are cheaper
            if condition == "used":
                price = round(price * 0.7, 2)
            elif condition == "refurbished":
                price = round(price * 0.8, 2)

            # Generate fake but realistic-looking URL
            item_id = rng.randint(100000000, 999999999)
            url = f"{base_url}{item_id}"

            listings.append(
                Listing.create(
                    source=f"{source_name} (Mock)",
                    price=price,
                    shipping=shipping,
                    condition=condition,
                    url=url,
                )
            )

        return listings
