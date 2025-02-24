import json
from .wallet import Wallet
from accounts.models.order import Order
from datetime import datetime

class User:
    """
    Represents a user with a Telegram user ID, wallet, and associated orders.
    """
    def __init__(self, telegram_userid):
        """
        Initialize a new User instance.

        :param telegram_userid: The Telegram user ID associated with the user.
        """
        self.telegram_userid = telegram_userid
        self._wallet = Wallet()  # Initialize user's wallet
        self._orders = []  # List to store user's orders

    @property
    def wallet(self):
        """
        Return the wallet associated with the user.
        """
        return self._wallet

    @property
    def orders(self):
        """
        Return the list of orders associated with the user.
        """
        return self._orders

    def add_order(self, order):
        """
        Add a new order to the user's orders list.

        :param order: The order object to add.
        """
        self._orders.append(order)

    def show_active_orders(self):
        """
        Generate and return a string representation of active orders.
        An active order is defined as one with status equal to ORDER_STATUS_OPEN.
        If the order has an order_manager, extended status details are included.

        :return: A string listing active orders or a message if there are none.
        """
        active_orders = []
        for order in self._orders:
            # Skip orders that are not open
            if order.status != order.ORDER_STATUS_OPEN:
                continue
            # If order has an order_manager attribute, retrieve its status details
            if hasattr(order, "order_manager"):
                status = order.order_manager.get_status()
                active_orders.append(
                    f"Order: {order.order_type.upper()} {order.cryptocurrency} | "
                    f"Status: {status.get('order_status')} | "
                    f"Price: {status.get('current_price')} | "
                    f"ROI: {status.get('roi', 0):.2f}% | "
                    f"Profit: ${status.get('profit', 0):.2f}"
                )
            else:
                # Fallback display for orders without an order_manager
                active_orders.append(
                    f"Order: {order.order_type.upper()} {order.cryptocurrency} | "
                    f"Entry: {order.entry_price} | Leverage: x{order.leverage}"
                )
        return "\n".join(active_orders) if active_orders else "No active orders."

    def __str__(self):
        """
        Return a string representation of the user.

        :return: A string with telegram_userid, wallet info, and number of orders.
        """
        return f'{self.telegram_userid} | {self._wallet} | {len(self._orders)} orders'


class UserManager:
    """
    Manages user data including loading and saving users to a JSON file.
    """
    def __init__(self, json_db_path="db.json"):
        """
        Initialize a new UserManager instance.

        :param json_db_path: JSON file path used for storing and loading user data.
        """
        self.json_db_path = json_db_path
        self.users = []

    def add_user(self, user: User):
        """
        Add a new user if a user with the same Telegram user ID does not already exist.

        :param user: The User object to add.
        """
        if self.get_user(user.telegram_userid) is None:
            self.users.append(user)

    def remove_user(self, telegram_userid: str):
        """
        Remove a user from the manager by their Telegram user ID.

        :param telegram_userid: The Telegram user ID of the user to remove.
        """
        self.users = [u for u in self.users if u.telegram_userid != telegram_userid]

    def get_user(self, telegram_userid: str):
        """
        Retrieve a user by their Telegram user ID.

        :param telegram_userid: The Telegram user ID to search for.
        :return: The User object if found, otherwise None.
        """
        for user in self.users:
            if user.telegram_userid == telegram_userid:
                return user
        return None

    def load_users(self):
        """
        Load users from the JSON file and recreate User and Order objects.
        If the file is not found, initializes with an empty user list.
        """
        try:
            with open(self.json_db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.users = []
            return

        self.users = []
        for user_data in data:
            telegram_userid = user_data.get("telegram_userid")
            wallet_balance = user_data.get("wallet_balance", 0.0)
            orders_data = user_data.get("orders", [])
            user = User(telegram_userid=telegram_userid)
            # Set wallet balance directly (assuming Wallet has a _balance attribute)
            user.wallet._balance = wallet_balance
            for od in orders_data:
                # Create an Order instance without calling its __init__ method
                order = Order.__new__(Order)
                order.owner = user
                order.cryptocurrency = od.get("cryptocurrency")
                order.amount = od.get("amount", 0.0)
                order.tp = od.get("tp")
                order.sl = od.get("sl")
                order.leverage = od.get("leverage", 1)
                order.order_type = od.get("order_type", "long")
                order.entry_price = od.get("entry_price", 0.0)
                order._status = od.get("status", Order.ORDER_STATUS_OPEN)
                open_at_str = od.get("open_at")
                order._open_at = datetime.fromisoformat(open_at_str) if open_at_str else None
                closed_at_str = od.get("closed_at")
                order._closed_at = datetime.fromisoformat(closed_at_str) if closed_at_str else None
                order.closed_profit = od.get("closed_profit")
                order.closed_roi = od.get("closed_roi")
                user.add_order(order)
            self.users.append(user)

    def save_users(self):
        """
        Save the current users and their associated orders to the JSON file.
        """
        data = []
        for user in self.users:
            user_dict = {
                "telegram_userid": user.telegram_userid,
                "wallet_balance": user.wallet.balance,
                "orders": []
            }
            for order in user.orders:
                order_data = {
                    "cryptocurrency": order.cryptocurrency,
                    "amount": order.amount,
                    "tp": order.tp,
                    "sl": order.sl,
                    "leverage": order.leverage,
                    "order_type": order.order_type,
                    "entry_price": order.entry_price,
                    "status": order.status,
                    "open_at": order._open_at.isoformat() if order._open_at else None,
                    "closed_at": order._closed_at.isoformat() if order._closed_at else None,
                    "closed_profit": getattr(order, "closed_profit", None),
                    "closed_roi": getattr(order, "closed_roi", None)
                }
                user_dict["orders"].append(order_data)
            data.append(user_dict)
        with open(self.json_db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
