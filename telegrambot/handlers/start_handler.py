from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from telegrambot.utils import main_menu_keyboard, get_or_create_user
from telegrambot.handlers.trade_handler import open_trade_crypto
from telegrambot.handlers.order_handler import view_open_trades, trade_history, account_status
from telegrambot.handlers.deposit_withdraw_handler import deposit_start, withdraw_start


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start the bot by sending a welcome message and displaying the main menu.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    """
    # Retrieve or create the user based on their Telegram ID
    get_or_create_user(str(update.effective_user.id))

    # Extract the user's first name for personalization
    first_name = update.effective_user.first_name

    # Send a welcome message with the main menu keyboard
    await update.message.reply_text(
        f"👋 Hello {first_name}!\n\n🌟 Welcome to the Ramztak Demo Trade Bot!\n\n"
        f"✨ We're excited to have you here. Please choose an option below to get started:",
        reply_markup=main_menu_keyboard()
    )


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Return the user to the main menu.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    """
    query = update.callback_query
    await query.answer()

    # Edit the current message to display the main menu
    await query.edit_message_text(
        "👋 Main Menu:\n\nPlease choose an option:",
        reply_markup=main_menu_keyboard()
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancel the current operation and end the conversation.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - End of conversation (ConversationHandler.END)
    """
    if update.callback_query:
        # Handle cancellation via callback query
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Operation canceled.")
    elif update.message:
        # Handle cancellation via direct message
        await update.message.reply_text("❌ Operation canceled.")
    return ConversationHandler.END


async def home_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle navigation to the home (main menu) by calling back_to_menu.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    """
    # Reuse the back_to_menu function to navigate to the main menu
    await back_to_menu(update, context)


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Dispatch actions based on the main menu callback data.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    """
    query = update.callback_query
    await query.answer()

    # Extract the callback data to determine the user's action
    data = query.data

    # Dispatch the appropriate handler based on the callback data
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
