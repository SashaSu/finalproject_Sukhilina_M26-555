import math
from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import config


class BaseApiClient(ABC):
    """Базовый клиент внешнего API"""
    @abstractmethod
    def fetch_rates(self):
        pass

class CoinGeckoClient(BaseApiClient):
    """Клиент API CoinGecko"""
    def __init__(self):
        self.url = config.coingecko_url
        self.timeout = config.request_timeout
        self.crypto_id_map = config.crypto_id_map
        self.last_metadata = {}

    def fetch_rates(self):
        ids = ",".join(self.crypto_id_map.values())

        try:
            response = requests.get(
                self.url,
                params={"ids": ids, "vs_currencies": "usd"},
                timeout=self.timeout,
            )
            if response.status_code == 401:
                raise ApiRequestError("Неверный API-ключ CoinGecko")
            if response.status_code == 429:
                raise ApiRequestError("Превышен лимит запросов CoinGecko")
            response.raise_for_status()
            data = response.json()
            rates = {}
            self.last_metadata = {}
            for currency, raw_id in self.crypto_id_map.items():
                rate = data[raw_id]["usd"]

                if (not isinstance(rate, (int, float)) or not math.isfinite(rate)
                        or rate <= 0):
                    raise ValueError(f"Некорректный курс {currency}")
                pair = f"{currency}_USD"
                rates[pair] = rate

                self.last_metadata[pair] = {
                    "raw_id": raw_id,
                    "request_ms": response.elapsed.total_seconds() * 1000,
                    "status_code": response.status_code,
                    "etag": response.headers.get("ETag"),
                }

            return rates
        except (requests.RequestException, ValueError, KeyError) as error:
            raise ApiRequestError(str(error)) from error


class ExchangeRateApiClient(BaseApiClient):
    """Клиент API ExchangeRate-API"""
    def __init__(self):
        self.url = config.exchangerate_api_url
        self.api_key = config.exchangerate_api_key
        self.base_currency = config.base_fiat_currency
        self.currencies = config.fiat_currencies
        self.timeout = config.request_timeout
        self.last_metadata = {}

    def fetch_rates(self):
        if not self.api_key:
            raise ApiRequestError("Не задан API-ключ ExchangeRate-API")
        url = f"{self.url}/{self.api_key}/latest/{self.base_currency}"
        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 401:
                raise ApiRequestError("Неверный API-ключ ExchangeRate-API")
            if response.status_code == 429:
                raise ApiRequestError("Превышен лимит запросов ExchangeRate-API")
            response.raise_for_status()
            data = response.json()
            if data.get("result") != "success":
                raise ValueError("ExchangeRate-API вернул ошибку")

            rates = {}
            self.last_metadata = {}

            for currency in self.currencies:
                source_rate = data["conversion_rates"][currency]
                if (not isinstance(source_rate, (int, float)) or
                        not math.isfinite(source_rate)
                        or source_rate <= 0):
                    raise ValueError(f"Некорректный курс {currency}")
                pair = f"{currency}_{self.base_currency}"
                rates[pair] = 1 / source_rate

                self.last_metadata[pair] = {
                    "raw_id": currency,
                    "request_ms": response.elapsed.total_seconds() * 1000,
                    "status_code": response.status_code,
                    "etag": response.headers.get("ETag"),
                }

            return rates

        except (requests.RequestException, ValueError, KeyError) as error:
            raise ApiRequestError(str(error)) from error