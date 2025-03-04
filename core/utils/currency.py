import requests
from django.conf import settings
from decimal import Decimal

def fetch_live_exchange_rate(target_currency):
    """Fetch the real-time exchange rate from an API."""
    api_key = settings.EXCHANGE_RATE_API_KEY  # Store API key in settings.py
    base_currency = "ETB"
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"

    try:
        response = requests.get(url)
        data = response.json()

        # Debugging: Print the entire response to verify structure
        print("API Response:", data)

        # Ensure 'conversion_rates' exists in the response
        if not isinstance(data, dict) or "conversion_rates" not in data:
            print("Error: 'conversion_rates' key not found in API response")
            return Decimal("1.0")  # Default to 1.0 if API fails

        # Extract exchange rate safely
        conversion_rates = data["conversion_rates"]
        exchange_rate = conversion_rates.get(target_currency)

        if exchange_rate is None:
            print(f"Warning: Exchange rate for {target_currency} not found. Using fallback.")
            return Decimal("1.0")  # Default to 1.0 if currency is missing

        return Decimal(str(exchange_rate))

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return Decimal("1.0")  # Default to 1.0 if API call fails
