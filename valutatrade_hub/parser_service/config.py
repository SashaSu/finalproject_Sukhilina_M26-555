import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
class ParserConfig:
    """Настройки сервиса получения курсов валют"""
    def __init__(self):
        self.exchangerate_api_key = os.getenv("EXCHANGERATE_API_KEY", "")
        self.coingecko_url = "https://api.coingecko.com/api/v3/simple/price"
        self.exchangerate_api_url = "https://v6.exchangerate-api.com/v6"
        self.base_fiat_currency = "USD"
        self.fiat_currencies = ("EUR", "RUB")
        self.crypto_currencies = ("BTC", "ETH")

        self.crypto_id_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
        }

        self.rates_file_path = Path("data/rates.json")
        self.history_file_path = Path("data/exchange_rates.json")
        self.request_timeout = 10

config = ParserConfig()