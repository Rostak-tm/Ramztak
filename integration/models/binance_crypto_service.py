import aiohttp
from .crypto_service_abstract import CryptoServiceAbstract


class BinanceCryptoService(CryptoServiceAbstract):
    """
    Service for retrieving cryptocurrency prices from the Binance API.

    This service implements the CryptoServiceAbstract interface by
    providing an asynchronous method to fetch the current price of a
    specified cryptocurrency.
    """

    def __init__(self, get_price_api_url):
        """
        Initialize the BinanceCryptoService with the base API URL.

        :param get_price_api_url: The base URL for fetching price information.
        """
        self.get_price_api_url = get_price_api_url

    async def get_price(self, currency: str) -> float:
        """
        Asynchronously fetch the current price of the specified cryptocurrency.

        :param currency: The cryptocurrency symbol (e.g., "BTC", "ETH").
        :return: The current price as a float.
        :raises Exception: If an error occurs during the HTTP request or if the currency is not found.
        """
        # Construct the URL by appending the uppercase currency symbol and "USDT" to the base URL.
        url = self.get_price_api_url + currency.upper() + "USDT"
        async with aiohttp.ClientSession() as session:
            # Send a GET request to the API URL.
            async with session.get(url) as response:
                # Check if the HTTP response status is OK (200).
                if response.status != 200:
                    # Retrieve the response text for error details.
                    text = await response.text()
                    # Raise an exception with status code and reason.
                    raise Exception(f"Error fetching price (status {response.status} {response.reason}): {text}")
                # Parse the JSON response.
                data = await response.json()
                # Extract the 'price' field from the JSON data.
                price = data.get("price")
                if price is None:
                    # Raise an exception if the price is not found in the response.
                    raise Exception("Currency not found!")
                # Return the price converted to a float.
                return float(price)
