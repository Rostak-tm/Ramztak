from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from telegrambot.utils import (
    get_cancel_keyboard,
    parse_positive_float,
    parse_positive_int,
    CRYPTO,
    TRADE_TYPE,
    AMOUNT,
    LEVERAGE,
    TP,
    SL,
    CONFIRM,
    POPULAR_CRYPTOS
)
from config import CRYPTO_SERVICE


async def open_trade_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Initiate the trade opening process by prompting the user to select a cryptocurrency.

    Displays a list of popular cryptocurrencies along with a "Cancel" button.

    :param update: Telegram update object containing the callback query.
    :param context: Telegram context object containing user data.
    :return: The conversation state identifier CRYPTO.
    """
    query = update.callback_query
    # Create a keyboard with popular cryptocurrencies and their corresponding emojis
    buttons = [
                  [InlineKeyboardButton(f"{sym} {emo}", callback_data=f"crypto_{sym}")]
                  for sym, emo in POPULAR_CRYPTOS
              ] + [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
    # Edit the message to display the cryptocurrency selection prompt
    await query.edit_message_text(
        "💱 Please select a cryptocurrency:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CRYPTO


async def crypto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the cryptocurrency selection by the user.

    Extracts the selected cryptocurrency symbol from the callback data,
    saves it in the context, and prompts the user to choose the trade type (Long or Short).

    :param update: Telegram update object containing the callback query.
    :param context: Telegram context object to store selected data.
    :return: The conversation state identifier TRADE_TYPE.
    """
    query = update.callback_query
    await query.answer()
    try:
        # Extract the cryptocurrency symbol from the callback data
        symbol = query.data.split("_")[1]
    except Exception:
        await query.edit_message_text("❌ Invalid selection.")
        return ConversationHandler.END

    # Save the selected cryptocurrency in the user data context
    context.user_data["crypto"] = symbol

    # Prepare a keyboard for selecting trade type
    buttons = [
        [
            InlineKeyboardButton("↗️ Long", callback_data="trade_long"),
            InlineKeyboardButton("↘️ Short", callback_data="trade_short")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    # Prompt user for trade type selection
    await query.edit_message_text(
        f"💱 Selected: {symbol}\n\nPlease select trade type:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return TRADE_TYPE


async def trade_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the trade type selection and prompt the user to enter the trade amount.

    Saves the selected trade type in context and then asks the user to input the USD amount.

    :param update: Telegram update object containing the callback query.
    :param context: Telegram context object to store selected data.
    :return: The conversation state identifier AMOUNT.
    """
    query = update.callback_query
    await query.answer()
    # Extract trade type from callback data (expects "trade_long" or "trade_short")
    context.user_data["trade_type"] = query.data.split("_")[-1]
    # Prompt user to enter the trade amount in USD with an option to cancel
    await query.edit_message_text(
        f"✅ Trade type selected: {context.user_data['trade_type'].capitalize()}\n\nEnter amount (USD):",
        reply_markup=get_cancel_keyboard()
    )
    return AMOUNT


async def amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the amount input by the user.

    Validates that the input is a positive float and then prompts the user to enter the leverage.

    :param update: Telegram update object containing the user's message.
    :param context: Telegram context object to store entered data.
    :return: The conversation state identifier LEVERAGE, or remains at AMOUNT if invalid.
    """
    from telegrambot.utils import send_with_cancel
    try:
        # Parse and validate the entered amount as a positive float
        context.user_data["amount"] = parse_positive_float(update.message.text.strip())
    except Exception:
        # If validation fails, send an error message with a cancel option
        await send_with_cancel(update, "❌ Invalid amount. Enter a number > 0:", context)
        return AMOUNT
    # Ask the user to enter the leverage
    await update.message.reply_text(
        "🔢 Enter leverage (e.g., 10,50,100):",
        reply_markup=get_cancel_keyboard()
    )
    return LEVERAGE


async def leverage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the leverage input by the user.

    Validates that the leverage is a positive integer and then prompts for the Take Profit (TP) price.

    :param update: Telegram update object containing the user's message.
    :param context: Telegram context object to store entered data.
    :return: The conversation state identifier TP, or remains at LEVERAGE if invalid.
    """
    from telegrambot.utils import send_with_cancel
    try:
        # Parse and validate the leverage as a positive integer
        context.user_data["leverage"] = parse_positive_int(update.message.text.strip())
    except Exception:
        # If validation fails, send an error message with a cancel option
        await send_with_cancel(update, "❌ Invalid leverage. Enter a positive integer:", context)
        return LEVERAGE
    # Prompt the user to enter the Take Profit (TP) price or skip
    await update.message.reply_text(
        "🎯 Enter Take Profit (TP) price or type 'skip':",
        reply_markup=get_cancel_keyboard()
    )
    return TP


async def tp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the Take Profit (TP) input by the user.

    If the user types 'skip', TP is set to None; otherwise, it is stored as a float.
    Then, the user is prompted to enter the Stop Loss (SL) price.

    :param update: Telegram update object containing the user's message.
    :param context: Telegram context object to store entered data.
    :return: The conversation state identifier SL.
    """
    text = update.message.text.strip()
    # Set TP to None if skipped, else convert to float
    context.user_data["tp"] = None if text.lower() == "skip" else float(text)
    # Prompt the user to enter the Stop Loss (SL) price or type 'skip'
    await update.message.reply_text(
        "🚫 Enter Stop Loss (SL) price or type 'skip':",
        reply_markup=get_cancel_keyboard()
    )
    return SL


async def sl_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the Stop Loss (SL) input by the user and confirm the trade details.

    If the user types 'skip', SL is set to None; otherwise, it is stored as a float.
    A summary of the trade is then composed and presented for confirmation.

    :param update: Telegram update object containing the user's message.
    :param context: Telegram context object to store entered data.
    :return: The conversation state identifier CONFIRM.
    """
    text = update.message.text.strip()
    # Set SL to None if skipped, else convert to float
    context.user_data["sl"] = None if text.lower() == "skip" else float(text)
    # Retrieve trade parameters from context
    sym = context.user_data.get("crypto")
    amt = context.user_data.get("amount")
    lev = context.user_data.get("leverage")
    tp_val = context.user_data.get("tp")
    sl_val = context.user_data.get("sl")
    # Build a summary message of the trade details
    summary = f"✅ Confirm trade:\n\n💱 Crypto: {sym}\n💵 Amount: ${amt}\n🔢 Leverage: x{lev}\n"
    if tp_val is not None:
        summary += f"🎯 TP: {tp_val}\n"
    if sl_val is not None:
        summary += f"🚫 SL: {sl_val}\n"
    # Prepare confirmation keyboard with "Confirm" and "Cancel" buttons
    buttons = [
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm_trade"),
         InlineKeyboardButton("Cancel", callback_data="cancel")]
    ]
    # Send the summary message with the inline keyboard
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(buttons))
    return CONFIRM


async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Confirm the trade and open a new order if all conditions are met.

    This function retrieves the current cryptocurrency price, verifies the user's balance,
    and then creates a new order. The user's data is saved after the trade is opened.

    :param update: Telegram update object containing the callback query.
    :param context: Telegram context object with collected trade details.
    :return: ConversationHandler.END to end the conversation.
    """
    query = update.callback_query
    await query.answer()
    # If user cancels the trade, return to the main menu
    if query.data == "cancel":
        from telegrambot.handlers.start_handler import back_to_menu
        return await back_to_menu(update, context)

    from telegrambot.utils import get_or_create_user, override_crypto_price
    tg_id = str(update.effective_user.id)
    # Retrieve or create the user object
    user = get_or_create_user(tg_id)
    sym = context.user_data["crypto"]
    amt = context.user_data["amount"]
    lev = context.user_data["leverage"]
    tp_val = context.user_data["tp"]
    sl_val = context.user_data["sl"]

    try:
        # Fetch the current price for the selected cryptocurrency
        price_value = await CRYPTO_SERVICE.get_price(sym)
    except Exception as e:
        await query.edit_message_text(f"❌ Error fetching price: {e}")
        return ConversationHandler.END

    # Validate the fetched price
    if not isinstance(price_value, float) or price_value <= 0:
        await query.edit_message_text("❌ Invalid price.")
        return ConversationHandler.END

    # Check if the user has sufficient balance for the trade amount
    if not user.wallet.has_enough_balance(amt):
        await query.edit_message_text("❌ Insufficient balance.")
        return ConversationHandler.END

    # Temporarily override the crypto price for the order creation context
    with override_crypto_price(price_value):
        try:
            from accounts.models.order import Order
            # Create a new Order instance which deducts the trade amount from the user's wallet
            Order(
                owner=user,
                cryptocurrency=sym,
                amount=amt,
                tp=tp_val,
                sl=sl_val,
                leverage=lev,
                order_type=context.user_data.get("trade_type", "long")
            )
            await query.edit_message_text("✅ Trade opened successfully!")
        except Exception as e:
            await query.edit_message_text(f"❌ Error opening trade: {e}")

    # Save the updated user data
    from telegrambot.utils import user_manager
    user_manager.save_users()
    return ConversationHandler.END
