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
from telegrambot.utils import CRYPTO, TRADE_TYPE, AMOUNT, LEVERAGE, TP, SL, CONFIRM, DEPOSIT_AMOUNT, WITHDRAW_AMOUNT

def main():
    """
    Initialize and run the Telegram bot application.

    This function sets up the bot by configuring logging, defining conversation handlers for
    various user interactions (e.g., trade opening, deposits, withdrawals), and registering
    command and callback query handlers. The bot is then started in polling mode.
    """
    # Configure logging to display bot-related messages with timestamps and log levels
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    # Build the Telegram bot application using the provided token
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler for the trade opening process
    trade_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(open_trade_crypto, pattern="^open_trade$")
        ],  # Entry point triggered when the user selects "open_trade"
        states={
            CRYPTO: [
                CallbackQueryHandler(cancel, pattern="^cancel$"),  # Allows cancellation at any step
                CallbackQueryHandler(crypto_handler, pattern="^crypto_")  # Handles cryptocurrency selection
            ],
            TRADE_TYPE: [
                CallbackQueryHandler(cancel, pattern="^cancel$"),  # Allows cancellation at any step
                CallbackQueryHandler(trade_type_handler, pattern="^(trade_long|trade_short)$")  # Handles trade type selection
            ],
            AMOUNT: [
                CallbackQueryHandler(cancel, pattern="^cancel$"),  # Allows cancellation at any step
                MessageHandler(filters.TEXT & ~filters.COMMAND, amount_handler)  # Handles trade amount input
            ],
            LEVERAGE: [
                CallbackQueryHandler(cancel, pattern="^cancel$"),  # Allows cancellation at any step
                MessageHandler(filters.TEXT & ~filters.COMMAND, leverage_handler)  # Handles leverage input
            ],
            TP: [
                CallbackQueryHandler(cancel, pattern="^cancel$"),  # Allows cancellation at any step
                MessageHandler(filters.TEXT & ~filters.COMMAND, tp_handler)  # Handles take-profit input
            ],
            SL: [
                CallbackQueryHandler(cancel, pattern="^cancel$"),  # Allows cancellation at any step
                MessageHandler(filters.TEXT & ~filters.COMMAND, sl_handler)  # Handles stop-loss input
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_handler, pattern="^confirm_trade$"),  # Confirms trade details
                CallbackQueryHandler(cancel, pattern="^cancel$")  # Allows cancellation at confirmation step
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]  # Fallback command to cancel the conversation
    )

    # Conversation handler for the deposit process
    deposit_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(deposit_start, pattern="^deposit$")
        ],  # Entry point triggered when the user selects "deposit"
        states={
            DEPOSIT_AMOUNT: [
                CallbackQueryHandler(cancel, pattern="^cancel$"),  # Allows cancellation at any step
                MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount_handler)  # Handles deposit amount input
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]  # Fallback command to cancel the conversation
    )

    # Conversation handler for the withdrawal process
    withdraw_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(withdraw_start, pattern="^withdraw$")
        ],  # Entry point triggered when the user selects "withdraw"
        states={
            WITHDRAW_AMOUNT: [
                CallbackQueryHandler(cancel, pattern="^cancel$"),  # Allows cancellation at any step
                MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount_handler)  # Handles withdrawal amount input
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]  # Fallback command to cancel the conversation
    )

    # Register callback query handlers for main menu and order management actions
    app.add_handler(CallbackQueryHandler(
        main_menu_callback, pattern="^(view_open_trades|trade_history|account_status|back_to_menu)$"
    ))  # Handles main menu navigation and related actions
    app.add_handler(CallbackQueryHandler(
        order_detail_handler, pattern="^order_detail_\\d+$"
    ))  # Handles viewing details of a specific order
    app.add_handler(CallbackQueryHandler(
        refresh_order_handler, pattern="^refresh_order_\\d+$"
    ))  # Handles refreshing the status of a specific order
    app.add_handler(CallbackQueryHandler(
        close_order_handler, pattern="^close_order_\\d+$"
    ))  # Handles closing a specific order
    app.add_handler(CallbackQueryHandler(
        back_to_orders_handler, pattern="^back_to_orders$"
    ))  # Handles returning to the orders list
    app.add_handler(CallbackQueryHandler(
        home_handler, pattern="^home$"
    ))  # Handles returning to the home/main menu

    # Add conversation handlers for trade, deposit, and withdrawal processes
    app.add_handler(trade_conv)
    app.add_handler(deposit_conv)
    app.add_handler(withdraw_conv)

    # Register basic command handlers for starting and canceling operations
    app.add_handler(CommandHandler("start", start))  # Handles the "/start" command
    app.add_handler(CommandHandler("cancel", cancel))  # Handles the "/cancel" command

    # Start the bot in polling mode
    app.run_polling()
