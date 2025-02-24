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
    Initiates the deposit process by prompting the user to enter a deposit amount.

    This function handles the callback query when the user selects the deposit option,
    edits the message to ask for the deposit amount, and displays a cancel keyboard.

    :param update: The update instance from Telegram.
    :param context: The context instance containing contextual data.
    :return: A constant indicating the next conversation state (DEPOSIT_AMOUNT).
    """
    # Retrieve the callback query from the update
    query = update.callback_query
    await query.answer()
    # Edit the message to prompt the user for a deposit amount with a cancel option
    await query.edit_message_text("💸 Enter deposit amount:", reply_markup=get_cancel_keyboard())
    return DEPOSIT_AMOUNT


async def deposit_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the deposit amount provided by the user.

    This function parses the input text as a positive float. If the value is invalid,
    it prompts the user to enter a valid amount. Upon successful parsing, it deposits
    the amount into the user's wallet, saves the updated user data, and notifies the user.

    :param update: The update instance from Telegram.
    :param context: The context instance containing contextual data.
    :return: The conversation state to end the conversation (ConversationHandler.END) or
             to re-prompt for the deposit amount.
    """
    try:
        # Parse and validate the deposit amount from the user's message
        amount = parse_positive_float(update.message.text.strip())
    except Exception:
        # If parsing fails, send an error message with a cancel option
        from telegrambot.utils import send_with_cancel
        await send_with_cancel(update, "❌ Invalid deposit amount. Enter a number > 0:", context)
        return DEPOSIT_AMOUNT

    # Retrieve or create a user object based on Telegram user id
    user = get_or_create_user(str(update.effective_user.id))
    # Deposit the validated amount into the user's wallet
    user.wallet.deposit(amount)

    # Save the updated user data
    from telegrambot.utils import user_manager
    user_manager.save_users()

    # Notify the user of a successful deposit
    await update.message.reply_text(f"💰 Deposited ${amount:.2f}!")
    return ConversationHandler.END


async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Initiates the withdrawal process by prompting the user to enter a withdrawal amount.

    This function handles the callback query when the user selects the withdrawal option,
    edits the message to ask for the withdrawal amount, and displays a cancel keyboard.

    :param update: The update instance from Telegram.
    :param context: The context instance containing contextual data.
    :return: A constant indicating the next conversation state (WITHDRAW_AMOUNT).
    """
    # Retrieve the callback query from the update
    query = update.callback_query
    await query.answer()
    # Edit the message to prompt the user for a withdrawal amount with a cancel option
    await query.edit_message_text("🏧 Enter withdrawal amount:", reply_markup=get_cancel_keyboard())
    return WITHDRAW_AMOUNT


async def withdraw_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the withdrawal amount provided by the user.

    This function parses the input text as a positive float. If the value is invalid,
    it prompts the user to enter a valid amount. Upon successful parsing, it attempts
    to withdraw the amount from the user's wallet. If the withdrawal fails (e.g., due to
    insufficient balance), an error is shown and the user is prompted again.

    :param update: The update instance from Telegram.
    :param context: The context instance containing contextual data.
    :return: The conversation state to end the conversation (ConversationHandler.END) or
             to re-prompt for the withdrawal amount.
    """
    try:
        # Parse and validate the withdrawal amount from the user's message
        amount = parse_positive_float(update.message.text.strip())
    except Exception:
        # If parsing fails, send an error message with a cancel option
        from telegrambot.utils import send_with_cancel
        await send_with_cancel(update, "❌ Invalid withdrawal amount. Enter a number > 0:", context)
        return WITHDRAW_AMOUNT

    # Retrieve or create a user object based on Telegram user id
    user = get_or_create_user(str(update.effective_user.id))
    try:
        # Attempt to withdraw the specified amount from the user's wallet
        user.wallet.withdraw(amount)
    except Exception as e:
        # If withdrawal fails, notify the user and prompt again
        await update.message.reply_text(f"❌ Error: {e}")
        return WITHDRAW_AMOUNT

    # Save the updated user data after withdrawal
    from telegrambot.utils import user_manager
    user_manager.save_users()

    # Notify the user of a successful withdrawal
    await update.message.reply_text(f"💸 Withdrew ${amount:.2f}!")
    return ConversationHandler.END
