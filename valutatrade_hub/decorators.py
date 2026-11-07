import inspect
from functools import wraps

from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.logging_config import setup_logging

logger = setup_logging()
settings = SettingsLoader()


def log_action(action, verbose=False):
    """Декоратор логирования операций"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            params = {}
            try:
                found_args = inspect.signature(func).bind(*args, **kwargs)
                params = found_args.arguments

                username = params.get("username")
                user_id = params.get("user_id")
                currency = params.get("currency")
                currency_code = getattr(currency, "code", currency)
                amount = params.get("amount")
                result = func(*args, **kwargs)
                if user_id is None and isinstance(result, dict):
                    user_id = result.get("user_id")
                if verbose and isinstance(result, tuple) and len(result) == 4:
                    old_balance, new_balance, rate, _ = result
                    base = settings.get("BASE_CURRENCY")
                    logger.info(
                        "action=%s username=%s user_id=%s "
                        "currency_code=%s amount=%s "
                        "balance=%s->%s rate=%s base=%s result=OK",
                        action, username, user_id, currency_code,
                        amount, old_balance, new_balance, rate, base)
                else:
                    logger.info(
                        "action=%s username=%s user_id=%s "
                        "currency_code=%s amount=%s result=OK",
                        action, username, user_id, currency_code,
                        amount)
                return result


            except Exception as error:
                logger.info(
                    "action=%s username=%s user_id=%s currency_code=%s amount=%s "
                    "result=ERROR error_type=%s error_message=%s",
                    action, params.get("username"), params.get("user_id"),
                    getattr(params.get("currency"), "code", params.get("currency")),
                    params.get("amount"), type(error).__name__, str(error))
                raise
        return wrapper
    return decorator