import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)
from config import TELEGRAM_BOT_TOKEN
from telegrambot.handlers.start_handler import start, main_menu_callback, cancel, home_handler
from telegrambot.handlers.trade_handler import (
    open_trade_crypto,
    crypto_handler,
    trade_type_handler,
    amount_handler,
    leverage_handler,
    tp_handler,
    sl_handler,
    confirm_handler
)
from telegrambot.handlers.deposit_withdraw_handler import (
    deposit_start,
    deposit_amount_handler,
    withdraw_start,
    withdraw_amount_handler
)
from telegrambot.handlers.order_handler import (
    trade_history,
    account_status,
    view_open_trades,
    order_detail_handler,
    refresh_order_handler,
    close_order_handler,
    back_to_orders_handler
)
from .utils import CRYPTO, TRADE_TYPE, AMOUNT, LEVERAGE, TP, SL, CONFIRM, DEPOSIT_AMOUNT, WITHDRAW_AMOUNT

def main():
    """
    Initialize and run the Telegram bot application.

    This function sets up logging, builds the bot application with the provided token,
    registers various conversation and callback query handlers for trading, deposits,
    withdrawals, and order management, and then starts polling for updates.
    """
    # Configure logging to display timestamp, module name, log level, and message
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    # Build the Telegram bot application using the bot token
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Define a conversation handler for the trade opening process
    trade_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(open_trade_crypto, pattern="^open_trade$")],
        states={
            # State for selecting cryptocurrency; callback data starts with "crypto_"
            CRYPTO: [CallbackQueryHandler(crypto_handler, pattern="^crypto_")],
            # State for selecting trade type; expects callback data "trade_long" or "trade_short"
            TRADE_TYPE: [CallbackQueryHandler(trade_type_handler, pattern="^(trade_long|trade_short)$")],
            # State for entering the trade amount; accepts any text that is not a command
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_handler)],
            # State for entering leverage; accepts any text that is not a command
            LEVERAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, leverage_handler)],
            # State for entering the Take Profit (TP) price
            TP: [MessageHandler(filters.TEXT & ~filters.COMMAND, tp_handler)],
            # State for entering the Stop Loss (SL) price
            SL: [MessageHandler(filters.TEXT & ~filters.COMMAND, sl_handler)],
            # State for confirming the trade; accepts callback data "confirm_trade" or "cancel"
            CONFIRM: [CallbackQueryHandler(confirm_handler, pattern="^(confirm_trade|cancel)$")],
        },
        # Fallback command to cancel the trade process
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Define a conversation handler for the deposit process
    deposit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(deposit_start, pattern="^deposit$")],
        states={
            # State for entering the deposit amount
            DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount_handler)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Define a conversation handler for the withdrawal process
    withdraw_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(withdraw_start, pattern="^withdraw$")],
        states={
            # State for entering the withdrawal amount
            WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount_handler)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Register callback query handlers for main menu and order management actions
    app.add_handler(CallbackQueryHandler(
        main_menu_callback, pattern="^(view_open_trades|trade_history|account_status|back_to_menu)$"
    ))
    app.add_handler(CallbackQueryHandler(
        order_detail_handler, pattern="^order_detail_\\d+$"
    ))
    app.add_handler(CallbackQueryHandler(
        refresh_order_handler, pattern="^refresh_order_\\d+$"
    ))
    app.add_handler(CallbackQueryHandler(
        close_order_handler, pattern="^close_order_\\d+$"
    ))
    app.add_handler(CallbackQueryHandler(
        back_to_orders_handler, pattern="^back_to_orders$"
    ))
    app.add_handler(CallbackQueryHandler(
        home_handler, pattern="^home$"
    ))

    # Add conversation handlers for trade, deposit, and withdrawal processes
    app.add_handler(trade_conv)
    app.add_handler(deposit_conv)
    app.add_handler(withdraw_conv)

    # Register basic command handlers for starting and canceling operations
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))

    # Start polling for updates from Telegram
    app.run_polling()
