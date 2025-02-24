import logging
from datetime import datetime
from contextlib import contextmanager
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from accounts.models.user import User, UserManager
from accounts.models.order import Order
from config import CRYPTO_SERVICE

# Define conversation states for the Telegram bot as integers.
CRYPTO, TRADE_TYPE, AMOUNT, LEVERAGE, TP, SL, CONFIRM, DEPOSIT_AMOUNT, WITHDRAW_AMOUNT = range(9)

# List of popular cryptocurrencies with associated emojis for quick selection.
POPULAR_CRYPTOS = [
    ("BTC", "💎"), ("ETH", "🔥"), ("XRP", "⚡️"), ("LTC", "🌙"),
    ("BCH", "💰"), ("ADA", "❤️"), ("DOT", "🔗"), ("LINK", "🔗"),
    ("XLM", "⭐️"), ("DOGE", "🐶")
]

# Instantiate the user manager and load existing users.
user_manager = UserManager()
user_manager.load_users()


def get_cancel_keyboard():
    """
    Create and return a cancel keyboard with a single "Cancel" button.

    :return: An InlineKeyboardMarkup object containing the cancel button.
    """
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])


def main_menu_keyboard():
    """
    Create and return the main menu keyboard markup.

    The main menu includes options for opening a trade, viewing open trades,
    trade history, deposit, withdrawal, and checking account status.

    :return: An InlineKeyboardMarkup object representing the main menu.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 Open Trade", callback_data="open_trade")],
        [InlineKeyboardButton("📃 View Open Trades", callback_data="view_open_trades")],
        [InlineKeyboardButton("📝 Trade History", callback_data="trade_history")],
        [InlineKeyboardButton("💸 Deposit", callback_data="deposit")],
        [InlineKeyboardButton("🏧 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("💼 Account Status", callback_data="account_status")]
    ])


async def send_with_cancel(update, text, context):
    """
    Send a message with a cancel option.

    This function determines whether the update is a message or a callback query,
    and then sends or edits the message with the provided text and a cancel keyboard.

    :param update: The Telegram update object (message or callback query).
    :param text: The text content to send.
    :param context: The Telegram context object.
    """
    kb = get_cancel_keyboard()
    if update.message:
        await update.message.reply_text(text, reply_markup=kb)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=kb)


def parse_positive_float(text: str) -> float:
    """
    Parse a string as a positive float.

    :param text: The string to parse.
    :return: The parsed float if it is positive.
    :raises ValueError: If the parsed number is not greater than zero.
    """
    value = float(text)
    if value <= 0:
        raise ValueError("Value must be greater than 0")
    return value


def parse_positive_int(text: str) -> int:
    """
    Parse a string as a positive integer.

    :param text: The string to parse.
    :return: The parsed integer if it is positive.
    :raises ValueError: If the parsed number is not greater than zero.
    """
    value = int(text)
    if value <= 0:
        raise ValueError("Value must be greater than 0")
    return value


def get_or_create_user(tg_id: str) -> User:
    """
    Retrieve an existing user by Telegram ID or create a new one if not found.

    :param tg_id: The Telegram user ID as a string.
    :return: The User object corresponding to the given Telegram ID.
    """
    # Reload users to ensure the latest data is used.
    user_manager.load_users()
    user = user_manager.get_user(tg_id)
    if not user:
        # Create a new user if one doesn't exist.
        user = User(tg_id)
        user_manager.add_user(user)
        user_manager.save_users()
    return user


def fallback_profit_roi(order: Order, current_price: float):
    """
    Calculate profit and ROI for an order using a fallback method.

    This function computes the profit and return on investment (ROI) based on the
    current price and order details, in case the order does not have a dedicated manager.

    :param order: The Order object.
    :param current_price: The current price of the cryptocurrency.
    :return: A tuple (profit, roi) representing the profit in dollars and ROI percentage.
    """
    # Determine the cryptocurrency amount based on order attributes.
    amt = (order.cryptocurrency_amount if hasattr(order, "cryptocurrency_amount") and order.entry_price
           else (order.amount / order.entry_price if order.entry_price else 0))

    # Calculate profit and ROI differently based on order type.
    if order.order_type == Order.ORDER_TYPE_LONG:
        profit = (current_price - order.entry_price) * amt * order.leverage
        roi = ((current_price / order.entry_price) - 1) * order.leverage * 100
    else:
        profit = (order.entry_price - current_price) * amt * order.leverage
        roi = (1 - (current_price / order.entry_price)) * order.leverage * 100
    return profit, roi


async def format_live_order(order: Order) -> str:
    """
    Format and return the details of an order as a human-readable string.

    For closed orders, it includes profit, ROI, and timestamps. For open orders, it
    fetches the current price to compute live profit and ROI.

    :param order: The Order object.
    :return: A formatted string representing the order details.
    """
    if order.status == Order.ORDER_STATUS_CLOSED:
        # Use stored closed order details.
        profit = getattr(order, "closed_profit", 0.0)
        roi = getattr(order, "closed_roi", 0.0)
        return (
            f"💱 Crypto: {order.cryptocurrency or 'N/A'}\n"
            f"📈 Type: {order.order_type.upper()}\n"
            f"💵 Entry: {order.entry_price:.2f}\n"
            f"💰 Profit: ${profit:.2f}\n"
            f"📊 ROI: {roi:.2f}%\n"
            f"🕒 Opened at: {order._open_at}\n"
            f"⏱️ Closed at: {order._closed_at}\n"
        )
    try:
        # Fetch the current price using the CRYPTO_SERVICE.
        cp = await CRYPTO_SERVICE.get_price(order.cryptocurrency)
    except Exception:
        cp = 0.0
    # Use the order's manager to calculate profit and ROI if available.
    if hasattr(order, "order_manager"):
        profit, roi = order.order_manager._calculate_profit_or_loss(cp)
    else:
        profit, roi = fallback_profit_roi(order, cp)
    return (
        f"💱 Crypto: {order.cryptocurrency or 'N/A'}\n"
        f"📈 Type: {order.order_type.upper()}\n"
        f"💵 Entry: {order.entry_price:.2f}\n"
        f"⏱️ Current: {cp:.2f}\n"
        f"📊 ROI: {roi:.2f}%\n"
        f"💰 Profit: ${profit:.2f}\n"
    )


@contextmanager
def override_crypto_price(price: float):
    """
    Temporarily override the cryptocurrency price returned by CRYPTO_SERVICE.

    This context manager replaces the CRYPTO_SERVICE.get_price function with a lambda
    that returns the specified price. After exiting the context, the original function is restored.

    :param price: The temporary price to use.
    """
    # Save the original get_price function.
    original = CRYPTO_SERVICE.get_price
    # Override get_price to always return the given price.
    CRYPTO_SERVICE.get_price = lambda currency: price
    try:
        yield
    finally:
        # Restore the original get_price function.
        CRYPTO_SERVICE.get_price = original
