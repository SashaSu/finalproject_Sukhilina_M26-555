import tomllib
from pathlib import Path

config_path = Path("pyproject.toml")
class SettingsLoader:
    """Загрузчик настроек приложения"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        config_path = Path("pyproject.toml")

        with config_path.open("rb") as file:
            config = tomllib.load(file)

        self._config = config["tool"]["valutatrade"]
        self._initialized = True

    def get(self, key, default=None):
        return self._config.get(key, default)
