import prompt
from prettytable import PrettyTable

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import (
    buy_currency,
    calc_portfolio,
    get_rate,
    login_user,
    register_user,
    sell_currency,
    show_portfolio,
)
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


def parse_register(parts):
    if len(parts) != 5 or parts[0] != "register" or parts[1] != "--username" \
            or parts[3] != "--password":
        raise ValueError("Неверный формат команды")
    return parts[2], parts[4]


def parse_login(parts):
    if len(parts) != 5 or parts[0] != "login" or parts[1] != "--username" \
            or parts[3] != "--password":
        raise ValueError("Неверный формат команды")
    return parts[2], parts[4]


def parse_show_portfolio(parts):
    if len(parts) == 1:
        return "USD"
    if len(parts) == 3 and parts[1] == "--base":
        return parts[2].upper()
    raise ValueError("Неверный формат команды")


def parse_buy(parts):
    if (len(parts) != 5 or parts[0] != "buy" or parts[1] != "--currency"
            or parts[3] != "--amount"):
        raise ValueError("Неверный формат команды")
    if not (2 <= len(parts[2]) <= 5) or not parts[2].isalpha():
        raise ValueError("Некорректный код валюты")
    currency = parts[2].upper()
    try:
        amount = float(parts[4])
    except ValueError:
        raise ValueError("Неверный тип amount")
    if amount <= 0:
        raise ValueError("amount должен быть положительным числом")
    return currency, amount


def parse_sell(parts):
    if (len(parts) != 5 or parts[0] != "sell" or parts[1] != "--currency"
            or parts[3] != "--amount"):
        raise ValueError("Неверный формат команды")
    if not (2 <= len(parts[2]) <= 5) or not parts[2].isalpha():
        raise ValueError("Некорректный код валюты")
    currency = parts[2].upper()
    try:
        amount = float(parts[4])
    except ValueError:
        raise ValueError("Неверный тип amount")
    if amount <= 0:
        raise ValueError("amount должен быть положительным числом")
    return currency, amount


def parse_rate(parts):
    if (len(parts) != 5 or parts[0] != "get-rate" or parts[1] != "--from"
            or parts[3] != "--to"):
        raise ValueError("Неверный формат команды")
    currency_1 = parts[2].upper()
    currency_2 = parts[4].upper()

    if not currency_1 or not currency_2:
        raise ValueError("Коды валют не должны быть пустыми")
    return currency_1, currency_2


def run():
    current_user = None
    while True:
        command = prompt.string("Введите команду: ")
        if not command.strip():
            continue
        parts = command.strip().split()
        parsed_command = parts[0]
        match parsed_command:
            case "register":
                try:
                    username, password = parse_register(parts)
                    print(register_user(username, password))
                except ValueError as error:
                    print(error)
            case "login":
                try:
                    login, password = parse_login(parts)
                    current_user = login_user(login, password)
                    print(f"Вы вошли как '{current_user['username']}'")
                except ValueError as error:
                    print(error)
            case "show-portfolio":
                try:
                    if current_user is None:
                        raise ValueError("Требуется авторизация")
                    base_currency = parse_show_portfolio(parts)
                    portfolio = show_portfolio(current_user["user_id"])
                    if not portfolio["wallets"]:
                        print("Кошельков нет")
                        continue
                    wallets, total = calc_portfolio(portfolio, base_currency)
                    table = PrettyTable()
                    table.field_names = ["Валюта", "Баланс",
                                         f"Стоимость ({base_currency})"]
                    for wallet in wallets:
                        table.add_row([wallet["currency"],
                        f"{wallet['balance']:.4f}", f"{wallet['value']:.2f}"])
                    print(f"Портфель пользователя '{current_user['username']}' "
                          f"(база: {base_currency}):")
                    print(table)
                    print(f"ИТОГО: {total:,.2f} {base_currency}")

                except ValueError as error:
                    print(error)
            case "buy":
                try:
                    if current_user is None:
                        raise ValueError("Требуется авторизация")
                    currency, amount = parse_buy(parts)
                    old_balance, new_balance, rate, purchase_value = (
                        buy_currency(current_user["user_id"], currency,amount))
                    print(f"Покупка выполнена: {amount:.4f} {currency} "
                          f""f"по курсу {rate:.2f} "
                          f"USD/{currency}")
                    print("Изменения в портфеле:")
                    print(f"- {currency}: было {old_balance:.4f} "
                          f"→ стало {new_balance:.4f}")
                    print(f"Оценочная стоимость покупки: {purchase_value:,.2f} USD")
                except CurrencyNotFoundError as error:
                    print(error)
                    print("Проверьте код валюты. Доступные валюты: "
                          "USD, EUR, RUB, BTC, ETH")
                except ValueError as error:
                    print(error)
            case "sell":
                try:
                    if current_user is None:
                        raise ValueError("Требуется авторизация")
                    currency, amount = parse_sell(parts)
                    old_balance, new_balance, rate, sale_value = (
                        sell_currency(current_user["user_id"], currency,amount))
                    print(f"Продажа выполнена: {amount:.4f} {currency} "
                          f"по курсу {rate:.2f} USD/{currency}")
                    print("Изменения в портфеле:")
                    print(f"- {currency}: было {old_balance:.4f} "
                          f"→ стало {new_balance:.4f}")
                    print(f"Оценочная выручка: {sale_value:,.2f} USD")
                except InsufficientFundsError as error:
                    print(error)
                except CurrencyNotFoundError as error:
                    print(error)
                    print("Проверьте код валюты. Доступные валюты: USD, EUR, "
                          "RUB, BTC, ETH")
                except ValueError as error:
                    print(error)
            case "get-rate":
                try:
                    if current_user is None:
                        raise ValueError("Требуется авторизация")
                    currency_1, currency_2 = parse_rate(parts)
                    rate, reverse_rate, updated_at = get_rate(currency_1, currency_2)
                    print(f"Курс {currency_1}→{currency_2}: "
                          f"{rate:.8f} (обновлено: {updated_at})")
                    print(f"Обратный курс {currency_2}→{currency_1}: "
                          f"{reverse_rate:.2f}")
                except CurrencyNotFoundError as error:
                    print(error)
                    print("Проверьте код валюты. Доступные валюты: USD, EUR, "
                          "RUB, BTC, ETH")
                except ApiRequestError as error:
                    print(error)
                    print("Попробуйте повторить запрос позже или "
                          "проверьте подключение к сети")
                except ValueError as error:
                    print(error)
            case "update-rates":
                try:
                    updated_count = RatesUpdater().update()
                    print(f"Курсы успешно обновлены. Получено записей: {updated_count}")
                except ApiRequestError as error:
                    print(error)
                except (OSError, ValueError) as error:
                    print(f"Ошибка сохранения курсов: {error}")
            case "show-rates":
                try:
                    rates = RatesStorage().load_rates()

                    table = PrettyTable()
                    table.field_names = [
                        "Валютная пара",
                        "Курс",
                        "Источник",
                        "Обновлено",
                    ]

                    for pair, data in rates.items():
                        if not isinstance(data, dict):
                            continue

                        if "rate" not in data:
                            continue

                        table.add_row([
                            pair,
                            data["rate"],
                            data.get("source", "Неизвестно"),
                            data.get("updated_at", "Неизвестно"),
                        ])

                    if table.rowcount == 0:
                        print("Курсы ещё не загружены. Используйте update-rates")
                    else:
                        print(table)

                except (OSError, ValueError, KeyError) as error:
                    print(f"Не удалось прочитать курсы: {error}")
            case _:
                print("Неизвестная команда")
