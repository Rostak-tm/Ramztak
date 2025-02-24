class CryptoServiceAbstract:
    """
    Abstract class for cryptocurrency price services.

    This class defines an interface for retrieving the current price of a cryptocurrency.
    Subclasses must implement the get_price method.
    """

    async def get_price(self, currency: str) -> float:
        """
        Asynchronously retrieve the current price for the given cryptocurrency.

        :param currency: The cryptocurrency symbol (e.g., "BTC", "ETH").
        :return: The current price as a float.
        :raises NotImplementedError: This method must be implemented by subclasses.
        """
        # Raise an error to enforce implementation in a subclass.
        raise NotImplementedError("This method should be implemented in subclasses")
