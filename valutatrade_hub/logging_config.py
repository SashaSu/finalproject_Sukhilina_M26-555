import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging():
    """Настройка логирования приложения"""
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir()
    logger = logging.getLogger("valutatrade_hub")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    handler = RotatingFileHandler(log_dir / "actions.log", maxBytes=5 * 1024 * 1024,
                                  backupCount=3, encoding="utf-8")
    formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s",
                                  datefmt="%Y-%m-%dT%H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger