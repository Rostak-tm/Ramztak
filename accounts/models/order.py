import asyncio
from datetime import datetime
from config import CRYPTO_SERVICE


class Order:
    """
    Represents a cryptocurrency trading order.
    """
    ORDER_STATUS_OPEN = "open"
    ORDER_STATUS_CLOSED = "closed"

    ORDER_TYPE_LONG = "long"
    ORDER_TYPE_SHORT = "short"

    def __init__(
            self,
            owner,
            cryptocurrency: str,
            amount: float,
            tp: float,
            sl: float,
            leverage: int,
            order_type: str
    ):
        """
        Initialize a new Order instance.

        :param owner: The user who owns the order.
        :param cryptocurrency: The cryptocurrency symbol (e.g., BTC, ETH).
        :param amount: The amount in USD to invest in the order.
        :param tp: The take profit price.
        :param sl: The stop loss price.
        :param leverage: The leverage multiplier.
        :param order_type: Type of the order ("long" or "short").
        :raises ValueError: If the owner has insufficient balance.
        """
        self.owner = owner
        self.cryptocurrency = cryptocurrency
        self.amount = amount
        self.tp = tp
        self.sl = sl
        self.leverage = leverage
        self.order_type = order_type
        self.crypto_service = CRYPTO_SERVICE

        # Get the current price for the cryptocurrency and calculate the amount of crypto purchased.
        self.entry_price = self.crypto_service.get_price(self.cryptocurrency)
        self.cryptocurrency_amount = amount / self.entry_price

        # Check if the owner has enough balance for this order.
        if not self.owner.wallet.has_enough_balance(amount):
            raise ValueError(f"Insufficient balance: User does not have {amount} USD")

        # Deduct the order amount from the user's wallet and register the order.
        self.owner.wallet.withdraw(amount)
        self.owner.add_order(self)

        # Set order opening time and initialize status.
        self._open_at = datetime.now()
        self._closed_at = None
        self._status = Order.ORDER_STATUS_OPEN

    @property
    def status(self):
        """
        Return the current status of the order.

        :return: The order's status.
        """
        return self._status

    @property
    def open_at(self):
        """
        Return the timestamp when the order was opened.

        :return: The order's opening datetime.
        """
        return self._open_at

    @property
    def closed_at(self):
        """
        Return the timestamp when the order was closed, if applicable.

        :return: The order's closing datetime or None if still open.
        """
        return self._closed_at

    def close_order(self, profit_dollar: float, roi: float):
        """
        Close the order and deposit the profit (or loss) back to the owner's wallet.

        :param profit_dollar: The profit (or negative loss) in dollars.
        :param roi: The return on investment as a percentage.
        :return: A dictionary containing order closure details.
        """
        if self._status == Order.ORDER_STATUS_CLOSED:
            return

        # Update order closure time and status.
        self._closed_at = datetime.now()
        self._status = Order.ORDER_STATUS_CLOSED

        # Deposit the original amount plus profit into the user's wallet.
        self.owner.wallet.deposit(self.amount + profit_dollar)
        return {
            "order_status": self._status,
            "roi": roi,
            "profit": profit_dollar,
            "closed_at": self._closed_at
        }

    def __str__(self):
        """
        Return a string representation of the order.

        :return: A string summarizing the order.
        """
        return f"{self.cryptocurrency}, ${self.amount}, {self.order_type}, {self._status}"


class OrderManager:
    """
    Manages the monitoring and execution of an order by periodically checking its status.
    """

    def __init__(self, order, polling_interval=0.5):
        """
        Initialize the OrderManager.

        :param order: The Order instance to manage.
        :param polling_interval: Time in seconds between price checks.
        """
        self.order = order
        self.polling_interval = polling_interval
        self.last_message = ""
        self._running = False

    async def start(self):
        """
        Start monitoring the order's price. This coroutine periodically polls for the current price,
        calculates profit or loss, and checks if any conditions for closing the order are met.

        :return: The last message logged during order monitoring.
        """
        self._running = True
        while self._running and self.order.status == self.order.ORDER_STATUS_OPEN:
            await asyncio.sleep(self.polling_interval)
            try:
                # Get the current price asynchronously
                current_price = await CRYPTO_SERVICE.get_price(self.order.cryptocurrency)
                profit, roi = self._calculate_profit_or_loss(current_price)
                self.last_message = (
                    f"Current Price: {current_price} | ROI: {roi:.2f}% | Profit: {profit:.2f}$"
                )

                # Check conditions for LONG orders.
                if self.order.order_type == self.order.ORDER_TYPE_LONG:
                    if self.order.tp and current_price >= self.order.tp:
                        self.last_message = f"Take Profit hit at {current_price}, closing order..."
                        self.order.close_order(profit, roi)
                        break
                    elif self.order.sl and current_price <= self.order.sl:
                        self.last_message = f"Stop Loss hit at {current_price}, closing order..."
                        self.order.close_order(profit, roi)
                        break
                    # Liquidation condition if no stop loss is set.
                    elif not self.order.sl and profit <= -self.order.amount:
                        self.last_message = f"Liquidation: Loss reached order amount at {current_price}, closing order..."
                        self.order.close_order(-self.order.amount, roi)
                        break

                # Check conditions for SHORT orders.
                elif self.order.order_type == self.order.ORDER_TYPE_SHORT:
                    if self.order.tp and current_price <= self.order.tp:
                        self.last_message = f"Take Profit hit at {current_price}, closing order..."
                        self.order.close_order(profit, roi)
                        break
                    elif self.order.sl and current_price >= self.order.sl:
                        self.last_message = f"Stop Loss hit at {current_price}, closing order..."
                        self.order.close_order(profit, roi)
                        break
                    elif not self.order.sl and profit <= -self.order.amount:
                        self.last_message = f"Liquidation: Loss reached order amount at {current_price}, closing order..."
                        self.order.close_order(-self.order.amount, roi)
                        break

            except Exception as e:
                # Log any error encountered during price monitoring.
                self.last_message = f"Error in price monitoring: {e}"
                break

        self._running = False
        return self.last_message

    def _calculate_profit_or_loss(self, current_price: float):
        """
        Calculate the profit or loss and ROI based on the current price.

        :param current_price: The latest price of the cryptocurrency.
        :return: A tuple containing profit in dollars and ROI percentage.
        """
        if self.order.order_type == self.order.ORDER_TYPE_LONG:
            profit_dollar = (
                    (current_price - self.order.entry_price)
                    * self.order.cryptocurrency_amount
                    * self.order.leverage
            )
            roi = ((current_price / self.order.entry_price) - 1) * self.order.leverage * 100
        elif self.order.order_type == self.order.ORDER_TYPE_SHORT:
            profit_dollar = (
                    (self.order.entry_price - current_price)
                    * self.order.cryptocurrency_amount
                    * self.order.leverage
            )
            roi = (1 - (current_price / self.order.entry_price)) * self.order.leverage * 100
        else:
            profit_dollar = 0.0
            roi = 0.0
        return profit_dollar, roi

    async def get_status(self):
        """
        Asynchronously retrieve the current status of the order including price, ROI, profit, and last message.

        :return: A dictionary with status information or error details if an exception occurs.
        """
        try:
            current_price = await CRYPTO_SERVICE.get_price(self.order.cryptocurrency)
            profit, roi = self._calculate_profit_or_loss(current_price)
            return {
                "current_price": current_price,
                "roi": roi,
                "profit": profit,
                "order_status": self.order.status,
                "last_message": self.last_message
            }
        except Exception as e:
            return {"error": str(e)}

    def stop(self):
        """
        Stop the order monitoring process.
        """
        self._running = False
