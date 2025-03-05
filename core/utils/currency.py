import requests
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)  # Use Django logging instead of print statements

def fetch_live_exchange_rate(target_currency):
    """Fetch real-time exchange rate from API with caching and error handling."""
    if target_currency == "ETB":
        return Decimal("1.0")  # No conversion needed for base currency

    cache_key = f"exchange_rate_{target_currency}"
    cached_rate = cache.get(cache_key)

    if cached_rate:
        return Decimal(str(cached_rate))  # Return cached value if available

    api_key = settings.EXCHANGE_RATE_API_KEY  # Store API key in settings.py
    base_currency = "ETB"
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"

    try:
        response = requests.get(url, timeout=5)  # Set timeout to prevent long delays
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        data = response.json()

        # Validate response structure
        if not isinstance(data, dict) or "conversion_rates" not in data:
            logger.warning("Invalid API response format: %s", data)
            return Decimal("1.0")

        # Extract exchange rate safely
        conversion_rates = data["conversion_rates"]
        exchange_rate = conversion_rates.get(target_currency)

        if exchange_rate is None:
            logger.warning("Exchange rate for %s not found. Using fallback.", target_currency)
            return Decimal("1.0")

        # Cache the exchange rate for 6 hours to reduce API calls
        cache.set(cache_key, exchange_rate, timeout=60 * 60 * 6)

        return Decimal(str(exchange_rate))

    except requests.exceptions.RequestException as e:
        logger.error("Request error fetching exchange rate: %s", e)
        return Decimal("1.0")  # Default to 1.0 if API call fails
