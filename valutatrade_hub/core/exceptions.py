class InsufficientFundsError(Exception):
    """Ошибка недостатка средств"""
    def __init__(self, available, required, code):
        message = (
            f"Недостаточно средств: доступно {available} {code}, "
            f"требуется {required} {code}"
        )
        super().__init__(message)


class CurrencyNotFoundError(Exception):
    """Ошибка неизвестной валюты"""
    def __init__(self, code):
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(Exception):
    """Ошибка запроса к API"""
    def __init__(self, reason):
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
