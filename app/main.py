import asyncio
from pathlib import Path
from typing import List

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.deduplicator import deduplicate_listings
from app.models import CompareRequest, CompareResponse, Listing
from app.normalizer import normalize_product
from app.sources.base import Source
from app.sources.ebay import EbaySource
from app.sources.mock import MockSource
from app.sources.serpapi import SerpApiSource

app = FastAPI(
    title="Price Comparison API",
    description="Compare prices across multiple marketplaces",
    version="0.1.0",
)

# Initialize all sources
SOURCES: List[Source] = [
    EbaySource(),
    SerpApiSource(),
    MockSource(),
]


@app.post("/compare", response_model=CompareResponse)
async def compare_prices(request: CompareRequest) -> CompareResponse:
    """
    Compare prices for a product across multiple sources.

    Returns up to 10 listings sorted by total price (cheapest first).
    """
    # Normalize the product name
    normalized = normalize_product(request.product_name)
    query = normalized.search_query

    # Get available sources
    available_sources = [s for s in SOURCES if s.is_available()]

    # Fetch from all sources in parallel
    search_tasks = [source.search(query) for source in available_sources]
    results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # Combine all listings
    all_listings: List[Listing] = []
    for result in results:
        if isinstance(result, list):
            all_listings.extend(result)

    # Deduplicate
    unique_listings = deduplicate_listings(all_listings)

    # Sort by total price (ascending)
    sorted_listings = sorted(unique_listings, key=lambda x: x.total_price)

    # Return top 10
    top_listings = sorted_listings[:10]

    return CompareResponse(
        query=query,
        results=top_listings,
    )


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    available_sources = [s.name for s in SOURCES if s.is_available()]
    return {
        "status": "healthy",
        "available_sources": available_sources,
    }


@app.get("/")
async def serve_frontend() -> FileResponse:
    """Serve the frontend HTML page."""
    html_path = Path(__file__).parent.parent / "index.html"
    return FileResponse(html_path)
