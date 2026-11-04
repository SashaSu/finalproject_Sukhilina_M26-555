import json
from datetime import datetime

from valutatrade_hub.core.models import User, generate_hash


def register_user(username, password):
    with open("data/users.json", "r", encoding="utf-8") as file:
        users = json.load(file)
        for user in users:
            if user["username"] == username:
                raise ValueError(f"Имя пользователя {username} уже занято")
    user_id = max((user["user_id"] for user in users), default=0) + 1
    user = User(user_id, username, password)
    users.append(user.make_dict())
    with open("data/users.json", "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4, ensure_ascii=False)
    with open("data/portfolios.json", "r", encoding="utf-8") as file:
        portfolios = json.load(file)
    portfolios.append({
        "user_id": user.user_id,
        "wallets": {}
    })
    with open("data/portfolios.json", "w", encoding="utf-8") as file:
        json.dump(portfolios, file, indent=4, ensure_ascii=False)

    return (f"Пользователь '{username}' зарегистрирован (id={user_id}). "
            f"Войдите: login --username"f" {username} --password **** ")


def login_user(username, password):
    with open("data/users.json", "r", encoding="utf-8") as file:
        users = json.load(file)
    for user in users:
        if user["username"] == username:
            password_hash = generate_hash(password, user["salt"])
            if password_hash != user["hashed_password"]:
                raise ValueError("Неверный пароль")
            return user
    raise ValueError(f"Пользователь '{username}' не найден")


def show_portfolio(user_id):
    with open("data/portfolios.json", "r", encoding="utf-8") as file:
        portfolios = json.load(file)
    for portfolio in portfolios:
        if portfolio["user_id"] == user_id:
            return portfolio
    raise ValueError("Портфель пользователя не найден")

def calc_portfolio(portfolio, base_currency):
    with open("data/rates.json", "r", encoding="utf-8") as file:
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

def buy_currency(user_id, currency, amount):
    with open("data/rates.json", "r", encoding="utf-8") as file:
        rates = json.load(file)
    if currency == "USD":
        currency_rate = 1.0
    elif f"{currency}_USD" in rates:
        currency_rate = rates[f"{currency}_USD"]["rate"]
    else:
        raise ValueError(f"Не удалось получить курс для {currency}")
    portfolio = show_portfolio(user_id)
    wallets = portfolio["wallets"]
    if currency not in wallets:
        wallets[currency] = {"balance": 0.0}
    old_balance = wallets[currency]["balance"]
    new_balance = wallets[currency]["balance"] + amount
    wallets[currency]["balance"] = new_balance
    with open("data/portfolios.json", "r", encoding="utf-8") as file:
        portfolios = json.load(file)
    for item in portfolios:
        if item["user_id"] == user_id:
            item["wallets"] = wallets
            break
    with open("data/portfolios.json", "w", encoding="utf-8") as file:
        json.dump(portfolios, file, indent=4, ensure_ascii=False)
    buy = amount * currency_rate
    return old_balance, new_balance, currency_rate, buy

def sell_currency(user_id, currency, amount):
    with open("data/rates.json", "r", encoding="utf-8") as file:
        rates = json.load(file)
    if currency == "USD":
        currency_rate = 1.0
    elif f"{currency}_USD" in rates:
        currency_rate = rates[f"{currency}_USD"]["rate"]
    else:
        raise ValueError(f"Не удалось получить курс для {currency}→USD")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    portfolio = show_portfolio(user_id)
    wallets = portfolio["wallets"]
    if currency not in wallets:
        raise ValueError(f"У вас нет кошелька '{currency}'")
    old_balance = wallets[currency]["balance"]
    if old_balance < amount:
        raise ValueError("Недостаточно средств")
    new_balance = old_balance - amount
    wallets[currency]["balance"] = new_balance
    with open("data/portfolios.json", "r", encoding="utf-8") as file:
        portfolios = json.load(file)
    for item in portfolios:
        if item["user_id"] == user_id:
            item["wallets"] = wallets
            break
    with open("data/portfolios.json", "w", encoding="utf-8") as file:
        json.dump(portfolios, file, indent=4, ensure_ascii=False)
    sale = amount * currency_rate
    return old_balance, new_balance, currency_rate, sale

def get_usd_rate(currency, rates):
    if currency == "USD":
        return 1.0
    key = f"{currency}_USD"
    if key not in rates:
        raise ValueError(f"Не удалось получить курс для {currency}→USD")
    return rates[key]["rate"]

def get_rate(currency_1, currency_2):
    if (not currency_1 or not currency_2 or currency_1 != currency_1.upper()
            or currency_2 != currency_2.upper()):
        raise ValueError("Коды валют должны быть непустыми и в верхнем регистре")
    with open("data/rates.json", "r", encoding="utf-8") as file:
        rates = json.load(file)
    try:
        from_rate = get_usd_rate(currency_1, rates)
        to_rate = get_usd_rate(currency_2, rates)
    except ValueError:
        raise ValueError(f"Курс {currency_1}→{currency_2} недоступен")
    times = []
    for currency in (currency_1, currency_2):
        if currency != "USD":
            updated_at = rates[f"{currency}_USD"]["updated_at"]
            times.append(datetime.fromisoformat(updated_at))
    now = datetime.now()
    if times and (now - min(times)).total_seconds() >= 300:
        raise ValueError(f"Курс {currency_1}→{currency_2} недоступен")
    rate = from_rate / to_rate
    reverse_rate = to_rate / from_rate
    if times:
        updated_at = min(times).strftime("%Y-%m-%d %H:%M:%S")
    else:
        updated_at = now.strftime("%Y-%m-%d %H:%M:%S")
    return rate, reverse_rate, updated_at