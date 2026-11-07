import logging
import time

from valutatrade_hub.parser_service.updater import RatesUpdater

logger = logging.getLogger("valutatrade_hub")

class RatesScheduler:
    """Планировщик обновления валютных курсов"""
    def __init__(self, interval=300):
        self.interval = interval
        self.updater = RatesUpdater()
    def start(self):
        logger.info("Планировщик обновления курсов запущен")
        while True:
            try:
                updated_count = self.updater.update()
                logger.info("Обновлено курсов: %s", updated_count)
            except Exception as error:
                logger.error("Ошибка планировщика: %s", error)
            time.sleep(self.interval)