from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegrambot.utils import get_or_create_user, format_live_order, fallback_profit_roi
from accounts.models.order import Order
from config import CRYPTO_SERVICE


async def trade_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display the user's trade history.

    This function retrieves the user's orders and formats them for display.
    If no orders are found, it informs the user that there is no trade history.

    :param update: The update object from Telegram.
    :param context: The context object containing additional data.
    :return: None. (Sends a message editing the current message with trade history.)
    """
    # Retrieve the callback query from the update and answer it
    query = update.callback_query
    await query.answer()

    # Get the user based on Telegram user id
    user = get_or_create_user(str(query.from_user.id))

    # Format the trade history if orders exist, otherwise show a default message
    msg = (
        "No trade history."
        if not user.orders
        else "\n---------------------------\n".join([await format_live_order(o) for o in user.orders])
    )

    # Create a keyboard with a "Back to Menu" button
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]])

    # Update the message text with the trade history and keyboard
    await query.edit_message_text(msg, reply_markup=kb)


async def account_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display the user's account status including wallet balance and number of orders.

    :param update: The update object from Telegram.
    :param context: The context object containing additional data.
    :return: None. (Sends a message editing the current message with account status.)
    """
    query = update.callback_query
    await query.answer()

    # Retrieve the user by Telegram user id
    user = get_or_create_user(str(query.from_user.id))

    # Prepare a message with account status details
    text = f"💼 Account Status:\n💰 Balance: ${user.wallet.balance:.2f}\n📋 Orders: {len(user.orders)}"

    # Create a keyboard with a "Back to Menu" button
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]])

    # Edit the message to show the account status
    await query.edit_message_text(text, reply_markup=kb)


async def view_open_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display all active (open) trades for the user.

    This function filters open orders and displays each with its basic details.
    A keyboard is provided to view detailed status for each order or to go back to the menu.

    :param update: The update object from Telegram.
    :param context: The context object containing additional data.
    :return: None. (Updates the message with open trades information.)
    """
    query = update.callback_query
    await query.answer()

    # Retrieve the user using their Telegram user id
    user = get_or_create_user(str(query.from_user.id))

    # Filter the orders to get only open orders
    open_orders = [o for o in user.orders if o.status == Order.ORDER_STATUS_OPEN]

    if not open_orders:
        # If no open orders, prepare a simple message and keyboard
        msg = "No active trades."
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]])
    else:
        msgs, buttons = [], []
        # Build a message and a corresponding button for each open order
        for i, o in enumerate(open_orders):
            msgs.append(
                f"Order {i + 1}:\n"
                f"💱 {o.cryptocurrency or 'N/A'}\n"
                f"📈 {o.order_type.upper()}\n"
                f"💵 Entry: {o.entry_price:.2f}\n"
                f"🔢 Leverage: x{o.leverage}"
            )
            buttons.append([InlineKeyboardButton(f"ℹ️ Status {i + 1}", callback_data=f"order_detail_{i}")])

        # Append a final button to return to the main menu
        buttons.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
        msg = "\n---------------------------\n".join(msgs)
        kb = InlineKeyboardMarkup(buttons)

    # Update the message with the open trades and the keyboard
    await query.edit_message_text(msg, reply_markup=kb)


async def order_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show detailed information for a selected open order.

    This function extracts the order index from the callback data,
    retrieves the corresponding open order, and displays its detailed status.

    :param update: The update object from Telegram.
    :param context: The context object containing additional data.
    :return: None. (Edits the current message to display order details.)
    """
    query = update.callback_query
    await query.answer()

    try:
        # Extract the order index from the callback data
        idx = int(query.data.split("_")[-1])
    except Exception:
        # Inform the user if the order index is invalid
        await query.edit_message_text("❌ Invalid order index.")
        return

    user = get_or_create_user(str(query.from_user.id))
    open_orders = [o for o in user.orders if o.status == Order.ORDER_STATUS_OPEN]

    # Validate if the index is within the range of open orders
    if idx < 0 or idx >= len(open_orders):
        await query.edit_message_text("❌ Order not found.")
        return

    order = open_orders[idx]
    # Retrieve live order details asynchronously
    details = await format_live_order(order)

    # Create a keyboard with options to close, refresh, or go back
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❌ Close", callback_data=f"close_order_{idx}"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_order_{idx}")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_orders")]
    ])

    # Update the message with order details and the keyboard
    await query.edit_message_text(details, reply_markup=kb)


async def refresh_order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Refresh the detailed view of an order.

    This function simply calls the order_detail_handler to update the order status.

    :param update: The update object from Telegram.
    :param context: The context object containing additional data.
    :return: None.
    """
    await order_detail_handler(update, context)


async def close_order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Close an open order.

    This function retrieves the selected order, fetches the current price,
    calculates profit and ROI, and then closes the order. The updated user data is saved.

    :param update: The update object from Telegram.
    :param context: The context object containing additional data.
    :return: None. (Updates the message after closing the order and refreshes the open trades view.)
    """
    query = update.callback_query
    await query.answer()

    try:
        # Extract the order index from the callback data
        idx = int(query.data.split("_")[-1])
    except Exception:
        await query.edit_message_text("❌ Invalid order index.")
        return

    user = get_or_create_user(str(query.from_user.id))
    open_orders = [o for o in user.orders if o.status == Order.ORDER_STATUS_OPEN]

    # Validate if the extracted index is valid
    if idx < 0 or idx >= len(open_orders):
        await query.edit_message_text("❌ Order not found.")
        return

    order = open_orders[idx]
    try:
        # Fetch the current price of the cryptocurrency for the order
        cp = await CRYPTO_SERVICE.get_price(order.cryptocurrency)
    except Exception as e:
        await query.edit_message_text(f"❌ Error getting price: {e}")
        return

    # Calculate profit and ROI using the order's manager if available, otherwise fallback
    if hasattr(order, "order_manager"):
        profit, roi = order.order_manager._calculate_profit_or_loss(cp)
    else:
        profit, roi = fallback_profit_roi(order, cp)

    # Close the order with the calculated profit and ROI
    order.close_order(profit, roi)
    order.closed_profit, order.closed_roi = profit, roi

    # Save the updated user data
    from telegrambot.utils import user_manager
    user_manager.save_users()

    # Inform the user that the order was closed and refresh the open trades view
    await query.edit_message_text("✅ Order closed successfully! Refreshing orders...")
    await view_open_trades(update, context)


async def back_to_orders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Return to the view displaying all open trades.

    :param update: The update object from Telegram.
    :param context: The context object containing additional data.
    :return: None. (Calls view_open_trades to update the message.)
    """
    await view_open_trades(update, context)
