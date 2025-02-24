from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegrambot.utils import get_or_create_user, format_live_order, fallback_profit_roi
from accounts.models.order import Order
from config import CRYPTO_SERVICE


async def trade_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display the user's trade history.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    """
    query = update.callback_query
    await query.answer()

    # Retrieve or create the user based on their Telegram ID
    user = get_or_create_user(str(query.from_user.id))

    # Generate the trade history message: If no orders exist, show a default message
    msg = (
        "No trade history."
        if not user.orders
        else "\n---------------------------\n".join([await format_live_order(o) for o in user.orders])
    )

    # Create a keyboard with a "Back to Menu" button
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]])

    # Update the message with the trade history and keyboard
    await query.edit_message_text(msg, reply_markup=kb)


async def account_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display the user's account status, including balance and active orders.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    """
    query = update.callback_query
    await query.answer()

    # Retrieve or create the user based on their Telegram ID
    user = get_or_create_user(str(query.from_user.id))

    # Prepare the account status text, showing balance and number of orders
    text = f"💼 Account Status:\n💰 Balance: ${user.wallet.balance:.2f}\n📋 Orders: {len(user.orders)}"

    # Create a keyboard with a "Back to Menu" button
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]])

    # Update the message with the account status and keyboard
    await query.edit_message_text(text, reply_markup=kb)


async def view_open_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display the user's open trades with options to view details or return to the menu.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    """
    query = update.callback_query
    await query.answer()

    # Retrieve or create the user based on their Telegram ID
    user = get_or_create_user(str(query.from_user.id))

    # Filter open orders from the user's order list
    open_orders = [o for o in user.orders if o.status == Order.ORDER_STATUS_OPEN]

    if not open_orders:
        # If no open orders exist, show a default message
        msg = "No active trades."
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]])
    else:
        msgs, buttons = [], []

        # Generate a summary for each open order
        for i, o in enumerate(open_orders):
            msgs.append(
                f"Order {i + 1}:\n"
                f"💱 {o.cryptocurrency or 'N/A'}\n"
                f"📈 {o.order_type.upper()}\n"
                f"💵 Entry: {o.entry_price:.2f}\n"
                f"🔢 Leverage: x{o.leverage}"
            )
            # Add a button for viewing order details
            buttons.append([InlineKeyboardButton(f"ℹ️ Status {i + 1}", callback_data=f"order_detail_{i}")])

        # Add a "Back to Menu" button at the end
        buttons.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])

        # Combine all messages into a single string
        msg = "\n---------------------------\n".join(msgs)
        kb = InlineKeyboardMarkup(buttons)

    # Update the message with the open trades summary and keyboard
    await query.edit_message_text(msg, reply_markup=kb)


async def order_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Display detailed information about a specific open order.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    """
    query = update.callback_query
    await query.answer()

    try:
        # Extract the order index from the callback data
        idx = int(query.data.split("_")[-1])
    except Exception:
        # Handle invalid index by showing an error message
        await query.edit_message_text("❌ Invalid order index.")
        return

    # Retrieve or create the user based on their Telegram ID
    user = get_or_create_user(str(query.from_user.id))

    # Filter open orders from the user's order list
    open_orders = [o for o in user.orders if o.status == Order.ORDER_STATUS_OPEN]

    if idx < 0 or idx >= len(open_orders):
        # Handle out-of-range index by showing an error message
        await query.edit_message_text("❌ Order not found.")
        return

    # Retrieve the selected order
    order = open_orders[idx]

    # Format the order details for display
    details = await format_live_order(order)

    # Create a keyboard with options to close, refresh, or go back
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❌ Close", callback_data=f"close_order_{idx}"),
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_order_{idx}")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_orders")]
    ])

    # Update the message with the order details and keyboard
    await query.edit_message_text(details, reply_markup=kb)


async def refresh_order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Refresh the details of a specific open order.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    """
    # Reuse the order detail handler to refresh the order
    await order_detail_handler(update, context)


async def close_order_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Close a specific open order and update the user's data.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    """
    query = update.callback_query
    await query.answer()

    try:
        # Extract the order index from the callback data
        idx = int(query.data.split("_")[-1])
    except Exception:
        # Handle invalid index by showing an error message
        await query.edit_message_text("❌ Invalid order index.")
        return

    # Retrieve or create the user based on their Telegram ID
    user = get_or_create_user(str(query.from_user.id))

    # Filter open orders from the user's order list
    open_orders = [o for o in user.orders if o.status == Order.ORDER_STATUS_OPEN]

    if idx < 0 or idx >= len(open_orders):
        # Handle out-of-range index by showing an error message
        await query.edit_message_text("❌ Order not found.")
        return

    # Retrieve the selected order
    order = open_orders[idx]

    try:
        # Get the current price of the cryptocurrency
        cp = await CRYPTO_SERVICE.get_price(order.cryptocurrency)
    except Exception as e:
        # Handle errors in fetching the price
        await query.edit_message_text(f"❌ Error getting price: {e}")
        return

    if hasattr(order, "order_manager"):
        # Calculate profit and ROI using the order manager
        profit, roi = order.order_manager._calculate_profit_or_loss(cp)
    else:
        # Use a fallback method to calculate profit and ROI
        profit, roi = fallback_profit_roi(order, cp)

    # Close the order and update its details
    order.close_order(profit, roi)
    order.closed_profit, order.closed_roi = profit, roi

    # Save the updated user data
    from telegrambot.utils import user_manager
    user_manager.save_users()

    # Notify the user that the order was closed successfully
    await query.edit_message_text("✅ Order closed successfully! Refreshing orders...")

    # Refresh the open trades view
    await view_open_trades(update, context)


async def back_to_orders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Return to the open trades view.
    :params update: Update - Telegram update object
    :params context: ContextTypes.DEFAULT_TYPE - Telegram context object
    """
    # Reuse the open trades view to return to the list of open orders
    await view_open_trades(update, context)
