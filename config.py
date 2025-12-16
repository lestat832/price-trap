import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # eBay Finding API credentials
    # Get your App ID at: https://developer.ebay.com/
    EBAY_APP_ID: Optional[str] = os.getenv("EBAY_APP_ID")

    # SerpAPI credentials (for Google Shopping)
    # Get your API key at: https://serpapi.com/
    SERPAPI_KEY: Optional[str] = os.getenv("SERPAPI_KEY")

    # Authentication credentials (required for production)
    AUTH_USERNAME: Optional[str] = os.getenv("AUTH_USERNAME")
    AUTH_PASSWORD: Optional[str] = os.getenv("AUTH_PASSWORD")

    # Enable mock mode for testing without API keys
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "false").lower() == "true"

    @property
    def ebay_available(self) -> bool:
        return bool(self.EBAY_APP_ID)

    @property
    def serpapi_available(self) -> bool:
        return bool(self.SERPAPI_KEY)

    @property
    def any_real_source_available(self) -> bool:
        return self.ebay_available or self.serpapi_available

    @property
    def auth_enabled(self) -> bool:
        return bool(self.AUTH_USERNAME and self.AUTH_PASSWORD)


settings = Settings()
