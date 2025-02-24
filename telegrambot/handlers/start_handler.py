from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from telegrambot.utils import main_menu_keyboard, get_or_create_user
from .trade_handler import open_trade_crypto
from .order_handler import view_open_trades, trade_history, account_status
from .deposit_withdraw_handler import deposit_start, withdraw_start


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start the bot by sending a welcome message and displaying the main menu.

    This function creates a user (if not already present) using the Telegram user ID,
    retrieves the user's first name, and sends a welcome message with a main menu keyboard.

    :param update: Telegram update object containing message data.
    :param context: Telegram context object for passing additional data.
    """
    # Create or retrieve the user based on their Telegram user ID
    get_or_create_user(str(update.effective_user.id))

    # Get the first name of the user for a personalized greeting
    first_name = update.effective_user.first_name

    # Send a welcome message along with the main menu keyboard
    await update.message.reply_text(
        f"👋 Hello {first_name}!\n\n🌟 Welcome to the Ramztak Demo Trade Bot!\n\n"
        f"✨ We're excited to have you here. Please choose an option below to get started:",
        reply_markup=main_menu_keyboard()
    )


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Return the user to the main menu.

    This function handles callback queries to navigate back to the main menu.

    :param update: Telegram update object containing callback query data.
    :param context: Telegram context object for passing additional data.
    """
    query = update.callback_query
    await query.answer()
    # Edit the message to display the main menu
    await query.edit_message_text(
        "👋 Main Menu:\n\nPlease choose an option:",
        reply_markup=main_menu_keyboard()
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancel the current operation and end the conversation.

    This function sends a cancellation message to the user and ends the conversation.

    :param update: Telegram update object.
    :param context: Telegram context object.
    :return: ConversationHandler.END to end the conversation.
    """
    # Check if the update contains a message or a callback query
    if update.message:
        await update.message.reply_text("❌ Operation canceled.")
    else:
        await update.callback_query.edit_message_text("❌ Operation canceled.")
    return ConversationHandler.END


async def home_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle navigation to the home (main menu) by calling back_to_menu.

    :param update: Telegram update object.
    :param context: Telegram context object.
    """
    await back_to_menu(update, context)


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Dispatch actions based on the main menu callback data.

    This function checks the callback data from the user and calls the appropriate handler:
      - "open_trade": Initiates a new trade.
      - "view_open_trades": Displays active trades.
      - "trade_history": Displays trade history.
      - "deposit": Initiates the deposit process.
      - "withdraw": Initiates the withdrawal process.
      - "account_status": Displays the account status.
      - "back_to_menu": Returns to the main menu.

    :param update: Telegram update object containing callback query data.
    :param context: Telegram context object.
    """
    query = update.callback_query
    await query.answer()

    # Retrieve the callback data to determine the action to take
    data = query.data
    if data == "open_trade":
        await open_trade_crypto(update, context)
    elif data == "view_open_trades":
        await view_open_trades(update, context)
    elif data == "trade_history":
        await trade_history(update, context)
    elif data == "deposit":
        await deposit_start(update, context)
    elif data == "withdraw":
        await withdraw_start(update, context)
    elif data == "account_status":
        await account_status(update, context)
    elif data == "back_to_menu":
        await back_to_menu(update, context)
