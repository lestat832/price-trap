import re
from dataclasses import dataclass
from typing import Optional


# Common electronics/consumer brands
KNOWN_BRANDS = {
    "sony", "apple", "samsung", "bose", "lg", "panasonic", "philips",
    "jbl", "sennheiser", "audio-technica", "beyerdynamic", "shure",
    "logitech", "razer", "corsair", "steelseries", "hyperx",
    "dell", "hp", "lenovo", "asus", "acer", "msi",
    "nvidia", "amd", "intel",
    "canon", "nikon", "fujifilm", "gopro",
    "dyson", "kitchenaid", "ninja", "instant pot", "vitamix",
    "nintendo", "playstation", "xbox", "microsoft",
    "google", "amazon", "meta", "oculus",
    "anker", "belkin", "tp-link", "netgear",
}


@dataclass
class NormalizedProduct:
    brand: Optional[str]
    model: Optional[str]
    full_query: str

    @property
    def search_query(self) -> str:
        """Return the best query string for API searches."""
        return self.full_query


def normalize_product(product_name: str) -> NormalizedProduct:
    """
    Extract brand and model from product name.
    Returns normalized product info for API searches.
    """
    # Clean up the input
    cleaned = product_name.strip()
    cleaned_lower = cleaned.lower()

    # Try to find a known brand
    brand = None
    for known_brand in KNOWN_BRANDS:
        # Match brand at word boundary
        pattern = rf"\b{re.escape(known_brand)}\b"
        if re.search(pattern, cleaned_lower):
            brand = known_brand.title()
            break

    # Try to extract model number (alphanumeric patterns like XM5, WH-1000XM5, A2234, etc.)
    model = None
    model_patterns = [
        r"\b([A-Z]{1,3}[-]?\d{2,4}[A-Z]{0,3}\d{0,2})\b",  # WH-1000XM5, XM5, A2234
        r"\b(\d{2,4}[A-Z]{1,3})\b",  # 1000XM, 65C1
        r"\b([A-Z]+\d+[A-Z]*\d*)\b",  # AirPods3, Galaxy22
    ]

    for pattern in model_patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            model = match.group(1).upper()
            break

    return NormalizedProduct(
        brand=brand,
        model=model,
        full_query=cleaned,
    )


def matches_product(listing_title: str, normalized: NormalizedProduct) -> bool:
    """
    Check if a listing title matches the normalized product.
    Used for filtering irrelevant results.
    """
    title_lower = listing_title.lower()
    query_lower = normalized.full_query.lower()

    # If we have a model number, require it to be present
    if normalized.model:
        model_lower = normalized.model.lower()
        # Allow for slight variations (with/without hyphens)
        model_no_hyphen = model_lower.replace("-", "")
        title_no_hyphen = title_lower.replace("-", "")

        if model_lower not in title_lower and model_no_hyphen not in title_no_hyphen:
            return False

    # If we have a brand, require it to be present
    if normalized.brand:
        if normalized.brand.lower() not in title_lower:
            return False

    return True
