# Price Comparison Service

A personal price comparison API that searches multiple marketplaces and returns the cheapest options.

## Quick Start (Mock Mode)

Run immediately without any API keys:

```bash
# Install dependencies
pip install -r requirements.txt

# Run with mock data
MOCK_MODE=true uvicorn app.main:app --reload --port 8000
```

Test it:
```bash
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Sony WH-1000XM5"}'
```

## API Endpoints

### POST /compare

Compare prices for a product.

**Request:**
```json
{
  "product_name": "Sony WH-1000XM5",
  "product_url": "optional-reference-url"
}
```

**Response:**
```json
{
  "query": "Sony WH-1000XM5",
  "results": [
    {
      "source": "eBay",
      "price": 279.99,
      "shipping": 0.0,
      "total_price": 279.99,
      "condition": "new",
      "url": "https://www.ebay.com/itm/..."
    }
  ]
}
```

### GET /health

Check service status and available sources.

## Configuration

Set environment variables or create a `.env` file:

```bash
# Enable mock mode (no API keys needed)
MOCK_MODE=true

# eBay Finding API
EBAY_APP_ID=your-ebay-app-id

# SerpAPI (Google Shopping)
SERPAPI_KEY=your-serpapi-key
```

## Getting API Keys

### eBay Finding API (Free)
1. Go to https://developer.ebay.com/
2. Create a developer account
3. Create an application to get your App ID (Production keys)
4. Set `EBAY_APP_ID` environment variable

### SerpAPI (Free tier: 100 searches/month)
1. Go to https://serpapi.com/
2. Create an account
3. Copy your API key from the dashboard
4. Set `SERPAPI_KEY` environment variable

## Data Sources

| Source | API | Notes |
|--------|-----|-------|
| eBay | Finding API | New + used items, shipping included |
| Google Shopping | SerpAPI | Aggregates multiple retailers |
| Mock | Built-in | Fake data for testing |

## Project Structure

```
price_comp/
├── app/
│   ├── main.py           # FastAPI application
│   ├── models.py         # Request/response models
│   ├── normalizer.py     # Product name parsing
│   ├── deduplicator.py   # Remove duplicate listings
│   └── sources/
│       ├── base.py       # Abstract source class
│       ├── ebay.py       # eBay integration
│       ├── serpapi.py    # Google Shopping integration
│       └── mock.py       # Mock data for testing
├── config.py             # Environment configuration
├── requirements.txt
└── README.md
```

## Adding New Sources

1. Create a new file in `app/sources/`
2. Extend the `Source` base class
3. Implement `name`, `is_available()`, and `search()`
4. Add the source to `SOURCES` list in `app/main.py`
