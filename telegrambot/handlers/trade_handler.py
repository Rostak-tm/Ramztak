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
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - Next conversation state (CRYPTO)
    """
    query = update.callback_query

    # Create buttons for popular cryptocurrencies with emojis and a cancel option
    buttons = [
                  [InlineKeyboardButton(f"{sym} {emo}", callback_data=f"crypto_{sym}")]
                  for sym, emo in POPULAR_CRYPTOS
              ] + [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]

    # Prompt the user to select a cryptocurrency
    await query.edit_message_text(
        "💱 Please select a cryptocurrency:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CRYPTO


async def crypto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the cryptocurrency selection by the user.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - Next conversation state (TRADE_TYPE)
    """
    query = update.callback_query
    await query.answer()

    try:
        # Extract the selected cryptocurrency symbol from the callback data
        symbol = query.data.split("_")[1]
    except Exception:
        # Handle invalid selection by showing an error message
        await query.edit_message_text("❌ Invalid selection.")
        return ConversationHandler.END

    # Store the selected cryptocurrency in the user's context data
    context.user_data["crypto"] = symbol

    # Create buttons for selecting trade type (Long/Short) and a cancel option
    buttons = [
        [
            InlineKeyboardButton("↗️ Long", callback_data="trade_long"),
            InlineKeyboardButton("↘️ Short", callback_data="trade_short")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    symbol_price = await CRYPTO_SERVICE.get_price(symbol)
    # Prompt the user to select a trade type
    await query.edit_message_text(
        f"💱 Selected: {symbol} - price (${symbol_price})\n\nPlease select trade type:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return TRADE_TYPE


async def trade_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the trade type selection and prompt the user to enter the trade amount.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - Next conversation state (AMOUNT)
    """
    query = update.callback_query
    await query.answer()

    # Store the selected trade type in the user's context data
    context.user_data["trade_type"] = query.data.split("_")[-1]

    # Prompt the user to enter the trade amount
    await query.edit_message_text(
        f"✅ Trade type selected: {context.user_data['trade_type'].capitalize()}\n\nEnter amount (USD):",
        reply_markup=get_cancel_keyboard()
    )
    return AMOUNT


async def amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the amount input by the user.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - Next conversation state (LEVERAGE) or retry state (AMOUNT)
    """
    from telegrambot.utils import send_with_cancel

    try:
        # Parse the user's input as a positive float and store it in the context data
        context.user_data["amount"] = parse_positive_float(update.message.text.strip())
    except Exception:
        # Handle invalid input by prompting the user again
        await send_with_cancel(update, "❌ Invalid amount. Enter a number > 0:", context)
        return AMOUNT

    # Prompt the user to enter the leverage value
    await update.message.reply_text(
        "🔢 Enter leverage (e.g., 10,50,100):",
        reply_markup=get_cancel_keyboard()
    )
    return LEVERAGE


async def leverage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the leverage input by the user.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - Next conversation state (TP) or retry state (LEVERAGE)
    """
    from telegrambot.utils import send_with_cancel

    try:
        # Parse the user's input as a positive integer and store it in the context data
        context.user_data["leverage"] = parse_positive_int(update.message.text.strip())
    except Exception:
        # Handle invalid input by prompting the user again
        await send_with_cancel(update, "❌ Invalid leverage. Enter a positive integer:", context)
        return LEVERAGE

    # Prompt the user to enter the Take Profit (TP) price
    await update.message.reply_text(
        "🎯 Enter Take Profit (TP) price or type 'skip':",
        reply_markup=get_cancel_keyboard()
    )
    return TP


async def tp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the Take Profit (TP) input by the user.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - Next conversation state (SL)
    """
    text = update.message.text.strip()

    # Store the Take Profit (TP) value in the context data (or None if skipped)
    context.user_data["tp"] = None if text.lower() == "skip" else float(text)

    # Prompt the user to enter the Stop Loss (SL) price
    await update.message.reply_text(
        "🚫 Enter Stop Loss (SL) price or type 'skip':",
        reply_markup=get_cancel_keyboard()
    )
    return SL


async def sl_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the Stop Loss (SL) input by the user and confirm the trade details.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - Next conversation state (CONFIRM)
    """
    text = update.message.text.strip()

    # Store the Stop Loss (SL) value in the context data (or None if skipped)
    context.user_data["sl"] = None if text.lower() == "skip" else float(text)

    # Retrieve trade details from the context data
    sym = context.user_data.get("crypto")
    amt = context.user_data.get("amount")
    lev = context.user_data.get("leverage")
    tp_val = context.user_data.get("tp")
    sl_val = context.user_data.get("sl")

    # Generate a summary of the trade details for confirmation
    summary = f"✅ Confirm trade:\n\n💱 Crypto: {sym}\n💵 Amount: ${amt}\n🔢 Leverage: x{lev}\n"
    if tp_val is not None:
        summary += f"🎯 TP: {tp_val}\n"
    if sl_val is not None:
        summary += f"🚫 SL: {sl_val}\n"

    # Create buttons for confirming or canceling the trade
    buttons = [
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm_trade"),
         InlineKeyboardButton("Cancel", callback_data="cancel")]
    ]

    # Prompt the user to confirm the trade
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(buttons))
    return CONFIRM


async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Confirm the trade and open a new order if all conditions are met.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    :returns: int - End of conversation (ConversationHandler.END)
    """
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        # If the user cancels, return to the main menu
        from telegrambot.handlers.start_handler import back_to_menu
        return await back_to_menu(update, context)

    from telegrambot.utils import get_or_create_user, override_crypto_price

    # Retrieve the user's Telegram ID and create or retrieve their user object
    tg_id = str(update.effective_user.id)
    user = get_or_create_user(tg_id)

    # Retrieve trade details from the context data
    sym = context.user_data["crypto"]
    amt = context.user_data["amount"]
    lev = context.user_data["leverage"]
    tp_val = context.user_data["tp"]
    sl_val = context.user_data["sl"]

    try:
        # Fetch the current price of the selected cryptocurrency
        price_value = await CRYPTO_SERVICE.get_price(sym)
    except Exception as e:
        # Handle errors in fetching the price
        await query.edit_message_text(f"❌ Error fetching price: {e}")
        return ConversationHandler.END

    if not isinstance(price_value, float) or price_value <= 0:
        # Validate the fetched price
        await query.edit_message_text("❌ Invalid price.")
        return ConversationHandler.END

    if not user.wallet.has_enough_balance(amt):
        # Check if the user has sufficient balance for the trade
        await query.edit_message_text("❌ Insufficient balance.")
        return ConversationHandler.END

    # Temporarily override the cryptocurrency price for trade confirmation
    with override_crypto_price(price_value):
        try:
            from accounts.models.order import Order

            # Create a new order with the provided trade details
            Order(
                owner=user,
                cryptocurrency=sym,
                amount=amt,
                tp=tp_val,
                sl=sl_val,
                leverage=lev,
                order_type=context.user_data.get("trade_type", "long")
            )

            # Notify the user that the trade was successfully opened
            await query.edit_message_text("✅ Trade opened successfully!")
        except Exception as e:
            # Handle errors during trade creation
            await query.edit_message_text(f"❌ Error opening trade: {e}")

    # Save the updated user data
    from telegrambot.utils import user_manager
    user_manager.save_users()

    return ConversationHandler.END
