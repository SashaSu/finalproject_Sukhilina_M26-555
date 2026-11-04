import hashlib
import secrets
from datetime import datetime


def validate_username(username):
    if username.strip() == "":
        raise ValueError("Имя не может быть пустым")


def validate_password(password):
    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")


def generate_hash(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()


class User:
    def __init__(self, user_id, username, password):
        validate_password(password)
        self._user_id = user_id
        self.username = username
        self._salt = secrets.token_hex(8)
        self._hashed_password = generate_hash(password, self._salt)
        self._registration_date = datetime.now()

    def get_user_info(self):
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date
        }

    def change_password(self, new_password: str):
        validate_password(new_password)
        self._salt = secrets.token_hex(8)
        self._hashed_password = generate_hash(new_password, self._salt)

    def verify_password(self, password: str):
        return self._hashed_password == generate_hash(password, self._salt)

    def make_dict(self):
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }

    def parse_sell(parts):
        if (len(parts) != 5 or parts[0] != "sell"
                or parts[1] != "--currency"
                or parts[3] != "--amount"):
            raise ValueError("Неверный формат команды")

        currency = parts[2].upper()

        try:
            amount = float(parts[4])
        except ValueError:
            raise ValueError("'amount' должен быть положительным числом")

        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        return currency, amount
    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        validate_username(value)
        self._username = value

    @property
    def user_id(self):
        return self._user_id

    @property
    def registration_date(self):
        return self._registration_date


def validate_balance(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Некорректный тип данных")
    if value < 0:
        raise ValueError("Значение баланса не может быть отрицательным")


def validate_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise TypeError("Сумма должна быть числом")

    if amount <= 0:
        raise ValueError("Сумма должна быть положительным числом")


class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code
        self.balance = balance

    def deposit(self, amount: float):
        validate_amount(amount)
        self._balance += amount

    def withdraw(self, amount: float):
        validate_amount(amount)
        if self._balance >= amount:
            self._balance -= amount
        else:
            raise ValueError("Недостаточно средств")

    def get_balance_info(self):
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        validate_balance(value)
        self._balance = value


class Portfolio:
    exchange_rates = {
        "USD": 1.0,
        "EUR": 1.08,
        "BTC": 65000.0,
        "ETH": 3500.0,
    }

    def __init__(self, user):
        self._user = user
        self._user_id = user.user_id
        self._wallets: dict[str, Wallet] = {}

    def add_currency(self, currency_code: str):
        if currency_code in self._wallets:
            raise ValueError(f"Кошелёк {currency_code} уже существует")
        self._wallets[currency_code] = Wallet(currency_code)

    def get_total_value(self, base_currency="USD"):
        base_rate = self.exchange_rates[base_currency]
        total = 0.0
        for currency_code, wallet in self._wallets.items():
            if currency_code not in self.exchange_rates:
                raise ValueError(f"Неизвестный курс валюты {currency_code}")
            currency_rate = self.exchange_rates[currency_code]
            total += wallet.balance * currency_rate / base_rate
        return total

    def get_wallet(self, currency_code):
        return self._wallets[currency_code]

    @property
    def user(self):
        return self._user

    @property
    def wallets(self):
        return self._wallets.copy()
