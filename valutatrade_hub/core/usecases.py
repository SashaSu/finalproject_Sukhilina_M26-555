import json
from datetime import datetime, timezone

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
)
from valutatrade_hub.core.models import User, Wallet, generate_hash
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.json_storage import load_json, save_json
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.parser_service.updater import RatesUpdater

settings = SettingsLoader()

@log_action("REGISTER")
def register_user(username, password):
    """Регистрация пользователя"""
    users = load_json(settings.get("USERS_FILE"))
    for user in users:
        if user["username"] == username:
            raise ValueError(f"Имя пользователя {username} уже занято")
    user_id = max((user["user_id"] for user in users), default=0) + 1
    user = User(user_id, username, password)
    users.append(user.make_dict())
    save_json(settings.get("USERS_FILE"), users)
    portfolios = load_json(settings.get("PORTFOLIOS_FILE"))
    portfolios.append({"user_id": user.user_id, "wallets": {}})
    save_json(settings.get("PORTFOLIOS_FILE"), portfolios)
    return (f"Пользователь '{username}' зарегистрирован (id={user_id}). "
        f"Войдите: login --username {username} --password ****")

@log_action("LOGIN")
def login_user(username, password):
    """Авторизация пользователя"""
    with open(settings.get("USERS_FILE"), "r", encoding="utf-8") as file:
        users = json.load(file)
    for user in users:
        if user["username"] == username:
            password_hash = generate_hash(password, user["salt"])
            if password_hash != user["hashed_password"]:
                raise ValueError("Неверный пароль")
            return user
    raise ValueError(f"Пользователь '{username}' не найден")

def show_portfolio(user_id):
    """Получение портфеля пользователя"""
    with open(settings.get("PORTFOLIOS_FILE"), "r", encoding="utf-8") as file:
        portfolios = json.load(file)
    for portfolio in portfolios:
        if portfolio["user_id"] == user_id:
            return portfolio
    raise ValueError("Портфель пользователя не найден")

def calc_portfolio(portfolio, base_currency):
    """Расчёт стоимости валют в портфеле"""
    with open(settings.get("RATES_FILE"), "r", encoding="utf-8") as file:
        rates = json.load(file)
    if base_currency != "USD" and f"{base_currency}_USD" not in rates:
        raise ValueError(f"Нет сведений о валюте '{base_currency}'")
    if base_currency == "USD":
        base_rate = 1.0
    else:
        base_rate = rates[f"{base_currency}_USD"]["rate"]
    result = []
    total = 0
    for currency, wallet in portfolio["wallets"].items():
        if currency == "USD":
            currency_rate = 1.0
        elif f"{currency}_USD" in rates:
            currency_rate = rates[f"{currency}_USD"]["rate"]
        else:
            raise ValueError(f"Неизвестная валюта '{currency}'")
        balance = wallet["balance"]
        cur_sum = balance * currency_rate / base_rate
        result.append({
            "currency": currency,
            "balance": balance,
            "value": cur_sum
        })

        total += cur_sum

    return result, total
@log_action("BUY", verbose=True)
def buy_currency(user_id, currency, amount):
    """Покупка валюты"""
    if amount <= 0:
        raise ValueError("amount должен быть положительным числом")
    currency_obj = get_currency(currency)
    currency_code = currency_obj.code
    with open(settings.get("RATES_FILE"), "r", encoding="utf-8") as file:
        rates = json.load(file)
    if currency_code == "USD":
        currency_rate = 1.0
    elif f"{currency_code}_USD" in rates:
        currency_rate = rates[f"{currency_code}_USD"]["rate"]
    else:
        raise ValueError(f"Не удалось получить курс для {currency_code}")
    portfolios = load_json(settings.get("PORTFOLIOS_FILE"))
    portfolio = next((item for item in portfolios if item["user_id"] == user_id), None)
    if portfolio is None:
        raise ValueError("Портфель пользователя не найден")
    wallets = portfolio["wallets"]
    if currency_code not in wallets:
        wallet = Wallet(currency_code)
    else:
        wallet = Wallet(currency_code, wallets[currency_code]["balance"])
    old_balance = wallet.balance
    wallet.deposit(amount)
    new_balance = wallet.balance
    wallets[currency_code] = wallet.get_balance_info()
    save_json(settings.get("PORTFOLIOS_FILE"), portfolios)
    buy = amount * currency_rate
    return old_balance, new_balance, currency_rate, buy
@log_action("SELL", verbose=True)
def sell_currency(user_id, currency, amount):
    """Продажа валюты"""
    if amount <= 0:
        raise ValueError("amount должен быть положительным числом")
    currency_obj = get_currency(currency)
    currency_code = currency_obj.code
    with open(settings.get("RATES_FILE"), "r", encoding="utf-8") as file:
        rates = json.load(file)
    if currency_code == "USD":
        currency_rate = 1.0
    elif f"{currency_code}_USD" in rates:
        currency_rate = rates[f"{currency_code}_USD"]["rate"]
    else:
        raise ValueError(f"Не удалось получить курс для {currency_code}→USD")
    portfolios = load_json(settings.get("PORTFOLIOS_FILE"))
    portfolio = next((item for item in portfolios if item["user_id"] == user_id), None)
    if portfolio is None:
        raise ValueError("Портфель пользователя не найден")
    wallets = portfolio["wallets"]
    if currency_code not in wallets:
        raise ValueError(f"У вас нет кошелька '{currency_code}'")

    wallet = Wallet(currency_code, wallets[currency_code]["balance"])
    old_balance = wallet.balance
    wallet.withdraw(amount)
    new_balance = wallet.balance

    wallets[currency_code] = wallet.get_balance_info()
    save_json(settings.get("PORTFOLIOS_FILE"), portfolios)
    sale = amount * currency_rate
    return old_balance, new_balance, currency_rate, sale

def get_usd_rate(currency, rates):
    """Получение курса валюты к доллару"""
    if currency == "USD":
        return 1.0
    key = f"{currency}_USD"
    if key not in rates:
        raise ApiRequestError(f"Курс для {currency}→USD отсутствует")
    return rates[key]["rate"]

def update_rates():
    """Обновление валютных курсов"""
    return RatesUpdater().update()
def get_rate(currency_1, currency_2):
    """Получение курса между двумя валютами"""
    if (not currency_1 or not currency_2 or currency_1 != currency_1.upper()
            or currency_2 != currency_2.upper()):
        raise ValueError("Коды валют должны быть непустыми и в верхнем регистре")

    get_currency(currency_1)
    get_currency(currency_2)

    rates = load_json(settings.get("RATES_FILE"))
    times = []

    for currency in (currency_1, currency_2):
        if currency != "USD":
            key = f"{currency}_USD"

            if key not in rates:
                update_rates()
                rates = load_json(settings.get("RATES_FILE"))

            updated_at = datetime.fromisoformat(rates[key]["updated_at"])
            times.append(updated_at)

    if times and (
        datetime.now(timezone.utc) - min(times)
    ).total_seconds() >= settings.get("RATES_TTL_SECONDS"):
        update_rates()
        rates = load_json(settings.get("RATES_FILE"))
        times = [
            datetime.fromisoformat(rates[f"{currency}_USD"]["updated_at"])
            for currency in (currency_1, currency_2)
            if currency != "USD"
        ]

    from_rate = get_usd_rate(currency_1, rates)
    to_rate = get_usd_rate(currency_2, rates)

    rate = from_rate / to_rate
    reverse_rate = to_rate / from_rate

    if times:
        updated_at = min(times).strftime("%Y-%m-%d %H:%M:%S")
    else:
        updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    return rate, reverse_rate, updated_at