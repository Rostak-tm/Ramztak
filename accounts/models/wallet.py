class Wallet:
    """
    A class representing a digital wallet for managing a balance.
    """
    def __init__(self):
        """
        Initialize the wallet with a starting balance of 0.00.
        """
        self._balance: float = 0.00  # Internal balance attribute

    @property
    def balance(self) -> float:
        """
        Retrieve the current balance of the wallet.

        :return: The current balance.
        """
        return self._balance

    def deposit(self, amount: float) -> None:
        """
        Deposit a specified amount into the wallet.

        :param amount: The amount to deposit.
        :raises ValueError: If the deposit amount is not greater than zero.
        """
        if amount < 0:
            raise ValueError("Deposit amount must be greater than zero")
        self._balance += amount  # Add the deposit amount to the current balance

    def withdraw(self, amount: float) -> None:
        """
        Withdraw a specified amount from the wallet.

        :param amount: The amount to withdraw.
        :raises ValueError: If the withdrawal amount is not greater than zero or if there is insufficient balance.
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero")
        if not self.has_enough_balance(amount):
            raise ValueError("Insufficient balance for wallet")
        self._balance -= amount  # Subtract the withdrawal amount from the current balance

    def has_enough_balance(self, amount: float) -> bool:
        """
        Check if the wallet has enough balance for a given amount.

        :param amount: The amount to check.
        :return: True if there is sufficient balance, otherwise False.
        """
        return self._balance >= amount

    def __repr__(self) -> str:
        """
        Return a string representation of the wallet including its balance.

        :return: A string displaying the wallet's balance.
        """
        return f"Wallet({self._balance:.2f})"
