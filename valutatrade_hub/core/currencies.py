from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


def validate_name(name):
    """Проверка названия валюты"""
    if name.strip() == "":
        raise ValueError("Строка пустая")

def validate_code(code):
    """Проверка кода валюты"""
    if (not (2 <= len(code) <= 5) or not code.isupper()
            or not code.isalpha() or " " in code):
        raise ValueError("Некорректный код валюты")

class Currency(ABC):
    """Базовая модель валюты"""
    def __init__(self, name, code):
        validate_name(name)
        validate_code(code)
        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self):
        """Получение описания валюты"""
        pass

class FiatCurrency(Currency):
    """Модель фиатной валюты"""
    def __init__(self, name, code, issuing_country):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self):
        """Получение информации о фиатной валюте"""
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"

class CryptoCurrency(Currency):
    """Модель криптовалюты"""
    def __init__(self, name, code, algorithm, market_cap):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self):
        """Получение информации о криптовалюте"""
        return (f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})")

CURRENCIES = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "European Union"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
}

def get_currency(code: str):
    """Получение валюты по коду"""
    if code not in CURRENCIES:
        raise CurrencyNotFoundError(f"Валюта {code} не найдена")
    return CURRENCIES[code]
