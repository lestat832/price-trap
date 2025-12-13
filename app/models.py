from typing import List, Optional

from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    product_name: str = Field(..., description="Product name to search for")
    product_url: Optional[str] = Field(None, description="Optional product URL for reference")


class Listing(BaseModel):
    source: str = Field(..., description="Source marketplace (e.g., 'eBay', 'Google Shopping')")
    price: float = Field(..., description="Item price in USD")
    shipping: float = Field(..., description="Shipping cost in USD")
    total_price: float = Field(..., description="Total price (item + shipping)")
    condition: str = Field(..., description="Item condition: new, used, refurbished, or unknown")
    url: str = Field(..., description="Purchase URL")

    @classmethod
    def create(
        cls,
        source: str,
        price: float,
        shipping: float,
        condition: str,
        url: str,
    ) -> "Listing":
        return cls(
            source=source,
            price=price,
            shipping=shipping,
            total_price=round(price + shipping, 2),
            condition=condition,
            url=url,
        )


class CompareResponse(BaseModel):
    query: str = Field(..., description="Normalized search query used")
    results: List[Listing] = Field(default_factory=list, description="Sorted listings (cheapest first)")
