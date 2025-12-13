from typing import List, Set
from urllib.parse import urlparse

from app.models import Listing


def deduplicate_listings(listings: List[Listing]) -> List[Listing]:
    """
    Remove duplicate listings based on URL.

    Keeps the first occurrence (which should be the cheapest
    if listings are pre-sorted).
    """
    seen_urls: Set[str] = set()
    unique_listings: List[Listing] = []

    for listing in listings:
        # Normalize URL for comparison (remove trailing slashes, query params)
        normalized_url = _normalize_url(listing.url)

        if normalized_url not in seen_urls:
            seen_urls.add(normalized_url)
            unique_listings.append(listing)

    return unique_listings


def _normalize_url(url: str) -> str:
    """Normalize URL for deduplication comparison."""
    try:
        parsed = urlparse(url)
        # Keep full URL including query params (needed for Google Shopping)
        # Only strip trailing slashes from path
        path = parsed.path.rstrip('/')
        query = f"?{parsed.query}" if parsed.query else ""
        normalized = f"{parsed.scheme}://{parsed.netloc}{path}{query}"
        return normalized.lower()
    except Exception:
        return url.lower()
