import logging
from datetime import datetime
from contextlib import contextmanager
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from accounts.models.user import User, UserManager
from accounts.models.order import Order
from config import CRYPTO_SERVICE
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN

# Conversation states
CRYPTO, TRADE_TYPE, AMOUNT, LEVERAGE, TP, SL, CONFIRM, DEPOSIT_AMOUNT, WITHDRAW_AMOUNT = range(9)

# Popular cryptocurrencies list
POPULAR_CRYPTOS = [
    ("BTC", "💎"), ("ETH", "🔥"), ("XRP", "⚡️"), ("LTC", "🌙"),
    ("BCH", "💰"), ("ADA", "❤️"), ("DOT", "🔗"), ("LINK", "🔗"),
    ("XLM", "⭐️"), ("DOGE", "🐶")
]

# Instantiate the user manager and load users
user_manager = UserManager()
user_manager.load_users()

def get_cancel_keyboard():
    """Return a cancel keyboard with a single 'Cancel' button."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])

def main_menu_keyboard():
    """Return the main menu keyboard markup."""
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
    :params update: Telegram update object
    :params text: str - Message text
    :params context: Telegram context object
    """
    kb = get_cancel_keyboard()
    if update.message:
        # If the update contains a message, reply to it with the cancel keyboard
        await update.message.reply_text(text, reply_markup=kb)
    else:
        # Otherwise, edit the existing message to include the cancel keyboard
        await update.callback_query.edit_message_text(text, reply_markup=kb)

def parse_positive_float(text: str) -> float:
    """
    Parse a string as a positive float.
    :params text: str - Input string
    :returns: float - Positive float value
    :raises ValueError: If value is not greater than 0
    """
    value = float(text)
    if value <= 0:
        raise ValueError("Value must be greater than 0")
    return value

def parse_positive_int(text: str) -> int:
    """
    Parse a string as a positive integer.
    :params text: str - Input string
    :returns: int - Positive integer value
    :raises ValueError: If value is not greater than 0
    """
    value = int(text)
    if value <= 0:
        raise ValueError("Value must be greater than 0")
    return value

def get_or_create_user(tg_id: str) -> User:
    """
    Retrieve an existing user by Telegram ID or create a new one if not found.
    :params tg_id: str - Telegram user ID
    :returns: User - Retrieved or newly created user object
    """
    user_manager.load_users()
    user = user_manager.get_user(tg_id)
    if not user:
        # If the user does not exist, create a new user and save it
        user = User(tg_id)
        user_manager.add_user(user)
        user_manager.save_users()
    return user

def fallback_profit_roi(order: Order, current_price: float):
    """
    Calculate profit and ROI for an order using a fallback method.
    :params order: Order - Order object
    :params current_price: float - Current cryptocurrency price
    :returns: tuple(float, float) - Profit and ROI
    """
    amt = (order.cryptocurrency_amount if hasattr(order, "cryptocurrency_amount") and order.entry_price
           else (order.amount / order.entry_price if order.entry_price else 0))
    if order.order_type == Order.ORDER_TYPE_LONG:
        # Calculate profit and ROI for a long position
        profit = (current_price - order.entry_price) * amt * order.leverage
        roi = ((current_price / order.entry_price) - 1) * order.leverage * 100
    else:
        # Calculate profit and ROI for a short position
        profit = (order.entry_price - current_price) * amt * order.leverage
        roi = (1 - (current_price / order.entry_price)) * order.leverage * 100
    return profit, roi

async def format_live_order(order: Order) -> str:
    """
    Format and return the details of an order as a human-readable string.
    :params order: Order - Order object
    :returns: str - Formatted order details
    """
    if order.status == Order.ORDER_STATUS_CLOSED:
        # If the order is closed, retrieve the closed profit and ROI
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
        # Fetch the current price of the cryptocurrency
        cp = await CRYPTO_SERVICE.get_price(order.cryptocurrency)
    except Exception:
        cp = 0.0
    if hasattr(order, "order_manager"):
        # Use the order manager to calculate profit and ROI if available
        profit, roi = order.order_manager._calculate_profit_or_loss(cp)
    else:
        # Use the fallback method to calculate profit and ROI
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
    :params price: float - The overridden price
    """
    original = CRYPTO_SERVICE.get_price
    CRYPTO_SERVICE.get_price = lambda currency: price
    try:
        yield
    finally:
        # Restore the original price-fetching function after use
        CRYPTO_SERVICE.get_price = original

async def send_message_to_user(telegram_userid: str, text: str):
    """
    Send a message directly to a user by their Telegram user ID.
    :param telegram_userid: str - Telegram user ID
    :param text: str - Message text
    """
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=telegram_userid, text=text)
