<h1 align="center">Ramztak 🚀</h1>

<p align="center">
  <img src="https://github.com/user-attachments/assets/2c90e251-4e11-4ca2-bbf1-5f7c8814ef53" alt="Ramztak Logo" width="300" style="border-radius: 45px;">
</p>


<p align="center">
  
![Python](https://img.shields.io/badge/Python-3.12.4-blue?logo=python) 
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-1.0.0-orange)

</p>

---
Welcome to **Ramztak** – a cutting-edge crypto trading simulator bot for Telegram! This project leverages robust trading logic to simulate real-time cryptocurrency trading using live Binance data. While a fully-featured Telegram interface is available, the core trading logic is designed to be modular. This means you, as a contributor, can easily develop and integrate additional interfaces (web, mobile, desktop, etc.) to expand the functionality of **Ramztak**. 💡

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Bot](#running-the-bot)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Live Cryptocurrency Prices:** Fetch real-time price updates directly from Binance. 📈
- **Simulated Trading:** Open and manage simulated trades (long or short) with support for leverage, take profit (TP), and stop loss (SL) settings.
- **User Account Management:** Automatically manage user profiles, wallet balances, and trade histories.
- **Interactive Telegram Interface:** Enjoy an intuitive, emoji-enhanced Telegram UI with inline keyboards for a smooth user experience. 📱
- **Modular Architecture:** The robust trading logic is separated from the interface layer, allowing you to easily develop and integrate additional interfaces. 🔧

---

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/Rostak-tm/Ramztak.git
   cd ramztak
   ```

2. **Set Up a Virtual Environment (Recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

Create a `.env` file in the project root and add the following configuration:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
BINANCE_CRYPTOSERVICE_API_URL=https://api.binance.com/api/v3/ticker/price?symbol=
```

Replace `your_telegram_bot_token_here` with your actual Telegram Bot Token, which you can obtain from [@BotFather](https://t.me/BotFather).

---

## Running the Bot

To launch the Telegram bot, simply run:

```bash
python main.py
```

The bot will start polling for updates. Open your Telegram app, search for your bot, and start interacting with it using commands like **/start**.

---

## Usage

- **/start:** Launch the bot and display the main menu.
- **Open Trade:** Simulate new trades by selecting a cryptocurrency, trade type, amount, leverage, TP, and SL.
- **View Open Trades:** Check your currently active trades.
- **Trade History:** Review your past trades.
- **Deposit/Withdraw:** Manage your virtual wallet balance.
- **Account Status:** Check your current balance and number of active trades.

Simply follow the on-screen prompts and use the interactive inline keyboards to navigate through the bot's features.

---

## Contributing

Contributions are highly encouraged! Whether you're looking to:

- **Enhance the Interface:** Develop additional user interfaces (e.g., a web dashboard, mobile app, etc.) to interact with the core trading logic.
- **Improve Functionality:** Optimize the trading logic or add new features.
- **Fix Bugs:** Identify and resolve issues to make **Ramztak** even better.

Feel free to fork the repository, create a new branch, and submit your pull requests. Let's build a more versatile and feature-rich trading simulator together! 🤝

---

## License

This project is licensed under the [MIT License](LICENSE).

---

Enjoy **Ramztak** – your gateway to simulated cryptocurrency trading in a fun, interactive, and risk-free environment🎉
