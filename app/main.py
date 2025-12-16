import asyncio
import secrets
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from config import settings

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

# HTTP Basic Auth (auto_error=False allows requests without credentials)
security = HTTPBasic(auto_error=False)


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials. Disabled if AUTH_USERNAME/AUTH_PASSWORD not set."""
    if not settings.auth_enabled:
        return  # Auth disabled for local development

    # If auth is enabled but no credentials provided, prompt for login
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    correct_username = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        settings.AUTH_USERNAME.encode("utf-8")
    )
    correct_password = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        settings.AUTH_PASSWORD.encode("utf-8")
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.post("/compare", response_model=CompareResponse)
async def compare_prices(
    request: CompareRequest,
    _: None = Depends(verify_credentials)
) -> CompareResponse:
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
async def health_check(_: None = Depends(verify_credentials)) -> dict:
    """Health check endpoint."""
    available_sources = [s.name for s in SOURCES if s.is_available()]
    return {
        "status": "healthy",
        "available_sources": available_sources,
    }


@app.get("/")
async def serve_frontend(_: None = Depends(verify_credentials)) -> FileResponse:
    """Serve the frontend HTML page."""
    html_path = Path(__file__).parent.parent / "index.html"
    return FileResponse(html_path)
