from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from telegrambot.utils import (
    get_cancel_keyboard,
    parse_positive_float,
    get_or_create_user,
    DEPOSIT_AMOUNT,
    WITHDRAW_AMOUNT
)


async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Prompt the user to enter a deposit amount.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - Next conversation state (DEPOSIT_AMOUNT)
    """
    query = update.callback_query
    await query.answer()

    # Prompt the user to enter a deposit amount with a cancel option
    await query.edit_message_text("💸 Enter deposit amount:", reply_markup=get_cancel_keyboard())
    return DEPOSIT_AMOUNT


async def deposit_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the deposit amount input and process the deposit.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - End of conversation or retry state (DEPOSIT_AMOUNT)
    """
    try:
        # Parse the user's input as a positive float
        amount = parse_positive_float(update.message.text.strip())
    except Exception:
        # If parsing fails, prompt the user again with an error message
        from telegrambot.utils import send_with_cancel
        await send_with_cancel(update, "❌ Invalid deposit amount. Enter a number > 0:", context)
        return DEPOSIT_AMOUNT

    # Retrieve or create the user based on their Telegram ID
    user = get_or_create_user(str(update.effective_user.id))

    # Process the deposit and update the user's wallet balance
    user.wallet.deposit(amount)

    # Save the updated user data
    from telegrambot.utils import user_manager
    user_manager.save_users()

    # Notify the user that the deposit was successful
    await update.message.reply_text(f"💰 Deposited ${amount:.2f}!")
    return ConversationHandler.END


async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Prompt the user to enter a withdrawal amount.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - Next conversation state (WITHDRAW_AMOUNT)
    """
    query = update.callback_query
    await query.answer()

    # Prompt the user to enter a withdrawal amount with a cancel option
    await query.edit_message_text("🏧 Enter withdrawal amount:", reply_markup=get_cancel_keyboard())
    return WITHDRAW_AMOUNT


async def withdraw_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the withdrawal amount input and process the withdrawal.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - End of conversation or retry state (WITHDRAW_AMOUNT)
    """
    try:
        # Parse the user's input as a positive float
        amount = parse_positive_float(update.message.text.strip())
    except Exception:
        # If parsing fails, prompt the user again with an error message
        from telegrambot.utils import send_with_cancel
        await send_with_cancel(update, "❌ Invalid withdrawal amount. Enter a number > 0:", context)
        return WITHDRAW_AMOUNT

    # Retrieve or create the user based on their Telegram ID
    user = get_or_create_user(str(update.effective_user.id))

    try:
        # Process the withdrawal and update the user's wallet balance
        user.wallet.withdraw(amount)
    except Exception as e:
        # Handle errors during withdrawal (e.g., insufficient balance)
        await update.message.reply_text(f"❌ Error: {e}")
        return WITHDRAW_AMOUNT

    # Save the updated user data
    from telegrambot.utils import user_manager
    user_manager.save_users()

    # Notify the user that the withdrawal was successful
    await update.message.reply_text(f"💸 Withdrew ${amount:.2f}!")
    return ConversationHandler.END
