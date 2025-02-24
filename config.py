import os
from dotenv import load_dotenv
from integration.models.binance_crypto_service import BinanceCryptoService

# Load environment variables from a .env file if available.
load_dotenv()

# Retrieve the Binance API URL from the environment
BINANCE_CRYPTOSERVICE_API_URL = os.getenv("BINANCE_CRYPTOSERVICE_API_URL")

# Retrieve the Telegram Bot token from the environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN",)

# Instantiate the BinanceCryptoService with the API URL.
CRYPTO_SERVICE = BinanceCryptoService(BINANCE_CRYPTOSERVICE_API_URL)
