import logging
from datetime import datetime, timezone

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.storage import RatesStorage

logger = logging.getLogger("valutatrade_hub")
class RatesUpdater:
    """Сервис обновления валютных курсов"""
    def __init__(self):
        self.clients = [
            CoinGeckoClient(),
            ExchangeRateApiClient(),
        ]
        self.storage = RatesStorage()

    def update(self):
        current_rates = {pair: data for pair, data in self.storage.load_rates().items()
            if isinstance(data, dict) and "rate" in data
        }
        history = self.storage.load_history()
        updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        updated_count = 0
        errors = []

        for client in self.clients:
            try:
                rates = client.fetch_rates()
                for pair, rate in rates.items():
                    metadata = client.last_metadata[pair]
                    source = ("CoinGecko" if isinstance(client, CoinGeckoClient)
                              else "ExchangeRate-API" )
                    record = {
                        "id": f"{pair}_{updated_at}",
                        "from_currency": pair.split("_")[0],
                        "to_currency": pair.split("_")[1],
                        "rate": rate,
                        "timestamp": updated_at,
                        "source": source,
                        "meta": metadata,
                    }
                    history.append(record)
                    current_rates[pair] = {
                        "rate": rate,
                        "updated_at": updated_at,
                        "source": source,
                    }
                    updated_count += 1
                logger.info(
                    "Обновлены курсы из %s: %s",
                    source,
                    len(rates),
                )
            except ApiRequestError as error:
                errors.append(str(error))
                logger.error("Ошибка обновления курсов: %s", error)
        if updated_count == 0:
            raise ApiRequestError(
                "Не удалось обновить курсы ни из одного источника"
            )
        self.storage.save_history(history)
        self.storage.save_rates(current_rates)
        logger.info("Обновление завершено. Получено курсов: %s", updated_count)
        return updated_count