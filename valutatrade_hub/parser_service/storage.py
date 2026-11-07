import json
import os
from pathlib import Path

from valutatrade_hub.parser_service.config import config


class RatesStorage:
    """Хранилище валютных курсов"""
    def __init__(self):
        self.rates_file = config.rates_file_path
        self.history_file = config.history_file_path

    def load_rates(self):
        """Загрузка актуальных курсов"""
        if not self.rates_file.exists():
            return {}

        with self.rates_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    def load_history(self):
        """Загрузка истории курсов"""
        if not self.history_file.exists():
            return []

        with self.history_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save_json(self, file_path, data):
        """Сохранение актуальных курсов"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = file_path.with_suffix(file_path.suffix + ".tmp")

        try:
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

            os.replace(temp_path, file_path)

        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def save_rates(self, rates):
        """Сохранение истории курсов"""
        self.save_json(self.rates_file, rates)

    def save_history(self, history):
        self.save_json(self.history_file, history)

storage = RatesStorage()