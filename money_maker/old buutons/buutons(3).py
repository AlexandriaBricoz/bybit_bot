# imports
from pybit.unified_trading import HTTP
from pybit.exceptions import InvalidRequestError
import telebot
from telebot import types
import pandas as pd
from tabulate import tabulate
import datetime
import time
import yaml
from robot import Robot
import threading

# Конфиги
form = yaml.safe_load(open('../form.yml', 'r'))

# Инициализация бота с токеном
session = HTTP(testnet=False, api_key=form['bybit']['api_key'], api_secret=form['bybit']['api_secret'])
bot = telebot.TeleBot(token=form['tg']['bot_token'])
r = Robot()

# Константы
sleep_time = form['time_period']  # счетчик
is_running = False


# Новая функция для проверки работоспособности бота - Горский
def check_bot():
    while True:
        time.sleep(300)  # Ожидание 5 минут
        if not is_running:
            bot.send_message(form['tg']['chat_id'], "Бот не работает. Перезапуск...")
            handle_stop(None)  # Остановить бота
            handle_strategy_1(None)  # Запустить стратегию 1


# запуск отслеживания бота в
# Запуск фоновой задачи для проверки состояния бота в потоке

threading.Thread(target=check_bot, daemon=True).start()


# Обработчики
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, text=f"Приветствую Вас!\n" \
                                           f"В меню слева доступны команды\n" \
                                           f'"Смена Формы" и "Запуск Стратегии"')


@bot.message_handler(commands=['chg_form'])
def form_chg(message):
    bot.send_message(message.chat.id,
                     text=f"Пожалуйста, подгрузите форму в формате form.yml\n"
                          f"По умолчанию используется форма разработчика.\n"
                          f"Пропустите шаг, если изменения не требуются."
                          f"Не нужно писать комментарии к форме.")


@bot.message_handler(content_types=['document'])
def proc_document(message):
    try:
        document_id = message.document.file_id
        document_path = bot.get_file(document_id).file_path
        document_name = message.document.file_name
        if document_name == 'form.yml':
            document_content = bot.download_file(document_path)
            document_content_decoded = document_content.decode('unicode_escape')
            if len(document_content_decoded) > 0:
                yaml_data = yaml.safe_load(document_content_decoded)
                if isinstance(yaml_data, dict):
                    inputed_attribs_ = list(yaml_data.keys())
                    sorted_inputed_attribs_ = sorted(inputed_attribs_)
                    attribs_ = ['time_period', 'symbol', 'isLeverage', 'min_value', 'values', 'ints', 'int_triggers',
                                'bybit', 'tg', 'deltaP']
                    sorted_attribs = sorted(attribs_)
                    bot.send_message(message.chat.id, f"{sorted_inputed_attribs_=}")
                    if sorted_inputed_attribs_ == sorted_attribs:
                        with open('../form.yml', 'w') as file:
                            yaml.dump(yaml_data, file)
                        bot.send_message(message.chat.id, 'Форма успешно загружена.\n' \
                                                          'Бот перезапущен с новыми параметрами.')
                        with open('../restart.txt', 'w') as file:
                            file.write(f'форма изменена_{datetime.datetime.now()}')
                    else:
                        bot.send_message(message.chat.id, 'Ошибка.\n' \
                                                          'Неверный состав атрибутов.')
                else:
                    bot.send_message(message.chat.id, 'Ошибка.\n' \
                                                      'Отсутствуют атрибуты.')

            else:
                bot.send_message(message.chat.id, 'Ошибка.\n' \
                                                  'Пустой документ.')
        else:
            bot.send_message(message.chat.id, 'Ошибка.\n' \
                                              'Некорректное название и расширение файла.\n'
                                              'Загрузите файл "form.yml"')
    except Exception:
        bot.send_message(message.chat.id, 'Ошибка.\n' \
                                          'Комментарии на русском после # в форме\n'
                                          'Уберите русский яз. и символ # из формы')


@bot.message_handler(commands=['strategy'])
def handle_strat(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    itembtn_str1 = types.KeyboardButton('Стратегия 1(int_0)')
    itembtn_str2 = types.KeyboardButton('Стратегия 2(market)')
    itembtn_buy_val1 = types.KeyboardButton('Купить value_1')
    itembtn_sell_val1 = types.KeyboardButton('Продать value_1')
    itembtn_balance = types.KeyboardButton('Баланс')
    itembtn_intervals = types.KeyboardButton('Интервалы')
    itembtn_orders = types.KeyboardButton('Текущие Ордера')
    itembtn_trades = types.KeyboardButton('Last Trades')
    itembtn_stop = types.KeyboardButton('STOP')
    itembtn_vkl = types.KeyboardButton('ВКЛ СЧЕТЧИК')
    itembtn_vikl = types.KeyboardButton('ВЫКЛ СЧЕТЧИК(del_orders)')
    markup.add(
        itembtn_str1, itembtn_str2,
        itembtn_buy_val1, itembtn_sell_val1,
        itembtn_balance, itembtn_intervals,
        itembtn_orders, itembtn_trades,
        itembtn_vkl, itembtn_vikl,
        itembtn_stop,
    )
    bot.send_message(message.chat.id, text="Пожалуйста, выберите статегию.", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Стратегия 1(int_0)")
def handle_strategy_1(message):
    global is_running
    if is_running:
        response = f"Стратегия уже выполняется.\n" \
                   f"Дождитесь выполнения стратегии."
        if message:
            bot.send_message(message.chat.id, text=response)
    else:
        is_running = True

        # t0 - block0(подготовка)
        enter_balance = round(r.calculate_total_balance(), 4)
        max_profit = None
        response = f"--Подготовка--\n" \
                   f"--Начальный баланс {enter_balance} USDC"
        if message:
            bot.send_message(message.chat.id, text=response)

        r.delete_all_orders()
        # r.create_order_11()
        # r.create_order_9()
        response = f"Закрыл все ордера - delete open orders.\n" \
            #          f"Выполнил order_11 прод. - продал все btc.\n"
        if message:
            bot.send_message(message.chat.id, text=response)
        time.sleep(sleep_time)

        # t1 - block1
        current_balance = r.calculate_total_balance()
        profit = round(current_balance - enter_balance, 3)
        max_profit = round(profit, 3)
        lo_price = r.check_last_order_price()
        if message:
            bot.send_message(message.chat.id, f"--Нахожусь в Блоке 1--\n" \
                                              f"--LO_price={lo_price}--\n" \
                                              f"--profit={profit} USDC, max={max_profit} USDC--")
            try:

                # Скворцов
                if (max_profit - profit) > float(form['deltaP']):
                    is_running = False
                    bot.send_message(message.chat.id, f' {is_running} 222222')
                    response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                    bot.send_message(message.chat.id, text=response)

                    # Отправка команды для перезапуска стратегии
                    handle_stop(message)
                    bot.send_message(message.chat.id, f'{response} 555555')
                    handle_strategy_1(message)

                    return

            except Exception as e:
                bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

        while is_running:
            metka = None
            delta = int(r.check_market_price() - r.check_last_order_price())
            if delta > form['ints']['int_0']:
                # r.create_order_enter_2()
                r.create_order_9()
                order_price = r.check_last_order_price()
                # r.create_order_1()
                # r.create_order_3()
                # r.create_order_4()
                if message:
                    bot.send_message(message.chat.id, f"delta={delta} ---> \n" \
                                                      f"Выполнил enter2-9 пок {order_price}\n" \
                                                      f"НеВыставил ордера 1,3,4")
                    # Сквроцов
                    current_balance = r.calculate_total_balance()
                    profit = round(current_balance - enter_balance, 3)
                    max_profit = profit if profit >= max_profit else max_profit

                    # Скворцов
                    try:

                        # Скворцов
                        if (max_profit - profit) > float(form['deltaP']):
                            is_running = False

                            response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                            bot.send_message(message.chat.id, text=response)

                            # Отправка команды для перезапуска стратегии
                            handle_stop(message)

                            handle_strategy_1(message)

                            return

                    except Exception as e:
                        bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                break
            elif delta < -form['ints']['int_9']:
                metka = r.check_market_price()
                if message:
                    bot.send_message(message.chat.id, f"delta={delta} ----> \n" \
                                                      f"Выставил метку по цене {metka}")
                    # Сквроцов
                    current_balance = r.calculate_total_balance()
                    profit = round(current_balance - enter_balance, 3)
                    max_profit = profit if profit >= max_profit else max_profit

                    # Скворцов
                    try:

                        # Скворцов
                        if (max_profit - profit) > float(form['deltaP']):
                            is_running = False

                            response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                            bot.send_message(message.chat.id, text=response)

                            # Отправка команды для перезапуска стратегии
                            handle_stop(message)

                            handle_strategy_1(message)

                            return

                    except Exception as e:
                        bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                break
            else:
                if message:
                    bot.send_message(message.chat.id, f"delta={delta} ---> hold")
                    # Сквроцов
                    current_balance = r.calculate_total_balance()
                    profit = round(current_balance - enter_balance, 3)
                    max_profit = profit if profit >= max_profit else max_profit

                    # Скворцов
                    try:

                        # Скворцов
                        if (max_profit - profit) > float(form['deltaP']):
                            is_running = False

                            response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                            bot.send_message(message.chat.id, text=response)

                            # Отправка команды для перезапуска стратегии
                            handle_stop(message)

                            handle_strategy_1(message)

                            return

                    except Exception as e:
                        bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                time.sleep(sleep_time)
        time.sleep(sleep_time)

        # t2 - blocks2/3/4
        side = None
        decision = None
        while is_running:
            if metka is None:
                side = r.check_last_order_side()
                lo_price = r.check_last_order_price()
                if side == 'Buy':
                    decision = 'Блок2'
                    if message:
                        bot.send_message(message.chat.id, f"Last Order = {side} по {lo_price} --->\n" \
                                                          f"Перехожу в {decision}")
                else:
                    decision = 'Блок3'
                    if message:
                        bot.send_message(message.chat.id, f"Last Order = {side} по {lo_price} --->\n" \
                                                          f"Перехожу в {decision}")
            else:
                side = 'metka'
                decision = 'Блок4'
                if message:
                    bot.send_message(message.chat.id, f"Last Order = {side} по {metka} --->\n" \
                                                      f"Перехожу в {decision}")

            if side == 'Buy':
                current_balance = r.calculate_total_balance()
                profit = round(current_balance - enter_balance, 3)
                max_profit = profit if profit >= max_profit else max_profit
                lo_price = r.check_last_order_price()
                if message:
                    bot.send_message(message.chat.id, f"--Нахожусь в Блоке 2--\n" \
                                                      f"--LO_price={lo_price}--\n" \
                                                      f"--profit={profit} USDC, max={max_profit} USDC--")

                    # Скворцов
                    try:

                        # Скворцов
                        if (max_profit - profit) > float(form['deltaP']):
                            is_running = False

                            response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                            bot.send_message(message.chat.id, text=response)

                            # Отправка команды для перезапуска стратегии
                            handle_stop(message)

                            handle_strategy_1(message)

                            return

                    except Exception as e:
                        bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                while is_running:
                    delta = int(r.check_market_price() - r.check_last_order_price())
                    try:
                        order_5_is_active = r.check_orders()['name'].str.contains('order5').any()
                    except Exception:
                        order_5_is_active = False
                    # if delta < 0:
                    if delta < form['ints']['int_3']:
                        r.delete_all_orders()
                        # r.create_order_3()
                        # r.create_order_5()
                        try:
                            r.create_order_10()
                        except:
                            # buy and sell q10
                            session.place_order(category='spot', symbol=form['symbol'], isLeverage=form['isLeverage'],
                                                orderType="Market", side='Sell', qty='btc_amnt', marketUnit='baseCoin')
                            # r.create_order_9()
                            r.create_order_10()
                        if message:
                            bot.send_message(message.chat.id,
                                             text=f"Закрыл все ордера - delete open orders.\n" \
                                                  f"delta={delta} --->\n" \
                                                  f"Выполнил order10-3 прод.")
                            # Сквроцов
                            current_balance = r.calculate_total_balance()
                            profit = round(current_balance - enter_balance, 3)
                            max_profit = profit if profit >= max_profit else max_profit

                            # Скворцов
                            try:

                                # Скворцов
                                if (max_profit - profit) > float(form['deltaP']):
                                    is_running = False

                                    response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"
                                    bot.send_message(message.chat.id, text=response)
                                    # Отправка команды для перезапуска стратегии
                                    handle_stop(message)

                                    handle_strategy_1(message)

                                    return

                            except Exception as e:
                                bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        break
                    elif order_5_is_active == False:
                        r.delete_all_orders()  # - александр попросил закомментить
                        r.create_order_3()
                        r.create_order_5()
                        if message:
                            bot.send_message(message.chat.id, f"delta={delta} и order5={order_5_is_active} --->\n" \
                                                              f"Выполнил order3 пок. выставил order5 прод.")
                            # Сквроцов
                            current_balance = r.calculate_total_balance()
                            profit = round(current_balance - enter_balance, 3)
                            max_profit = profit if profit >= max_profit else max_profit

                            # Скворцов
                            try:

                                # Скворцов
                                if (max_profit - profit) > float(form['deltaP']):
                                    is_running = False

                                    response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"
                                    bot.send_message(message.chat.id, text=response)
                                    # Отправка команды для перезапуска стратегии
                                    handle_stop(message)

                                    handle_strategy_1(message)

                                    return

                            except Exception as e:
                                bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        break
                    else:
                        if delta > form['ints']['int_4']:
                            r.create_order_4()
                            if message:
                                bot.send_message(message.chat.id, f"delta={delta}. Выполнил order4")
                                # Сквроцов
                                current_balance = r.calculate_total_balance()
                                profit = round(current_balance - enter_balance, 3)
                                max_profit = profit if profit >= max_profit else max_profit

                                # Скворцов
                                try:

                                    # Скворцов
                                    if (max_profit - profit) > float(form['deltaP']):
                                        is_running = False

                                        response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                                        bot.send_message(message.chat.id, text=response)

                                        # Отправка команды для перезапуска стратегии
                                        handle_stop(message)

                                        handle_strategy_1(message)

                                        return

                                except Exception as e:
                                    bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                            break
                        else:
                            if message:
                                bot.send_message(message.chat.id,
                                                 f"delta={delta} и order5={order_5_is_active} ---> hold")
                                # Скворцов
                                if order_5_is_active:
                                    try:
                                        delta = int(r.check_market_price() - r.check_last_order_price())
                                        if delta > form['ints']['int_1']:
                                            r.delete_all_orders()
                                            r.create_order_1()
                                            r.create_order_5()
                                            bot.send_message(message.chat.id, "Удалил ордера и созадл ордер 1 и 5")
                                        else:
                                            bot.send_message(message.chat.id, "Делаю STOP - Стратегия 2")
                                            handle_stop(message)
                                            handle_strategy_2(message)
                                            return
                                    except Exception as e:
                                        bot.send_message(message.chat.id,
                                                         f"Произошла непредвиденная ошибка во второй правке: {e}")
                                # Скворцов 1111111
                                current_balance = r.calculate_total_balance()
                                profit = round(current_balance - enter_balance, 3)
                                max_profit = profit if profit >= max_profit else max_profit

                                # Скворцов
                                try:

                                    # Скворцов
                                    if (max_profit - profit) > float(form['deltaP']):
                                        is_running = False

                                        response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                                        bot.send_message(message.chat.id, text=response)

                                        # Отправка команды для перезапуска стратегии
                                        handle_stop(message)

                                        handle_strategy_1(message)

                                        return

                                except Exception as e:
                                    bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")
                                # 1111111

                        time.sleep(sleep_time)
                time.sleep(sleep_time)

            elif side == 'Sell':
                current_balance = r.calculate_total_balance()
                profit = round(current_balance - enter_balance, 3)
                max_profit = profit if profit >= max_profit else max_profit
                lo_price = r.check_last_order_price()
                if message:
                    bot.send_message(message.chat.id, f"--Нахожусь в Блоке 3--\n" \
                                                      f"--LO_price={lo_price}--\n" \
                                                      f"--profit={profit} USDC, max={max_profit} USDC--")

                    # Скворцов
                    try:

                        # Скворцов
                        if (max_profit - profit) > float(form['deltaP']):
                            is_running = False

                            response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                            bot.send_message(message.chat.id, text=response)
                            # Отправка команды для перезапуска стратегии
                            handle_stop(message)

                            handle_strategy_1(message)

                            return

                    except Exception as e:
                        bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                r.delete_all_orders()
                if message:
                    bot.send_message(message.chat.id, "Закрыл все ордера - delete open orders")
                    # Сквроцов
                    current_balance = r.calculate_total_balance()
                    profit = round(current_balance - enter_balance, 3)
                    max_profit = profit if profit >= max_profit else max_profit

                    # Скворцов
                    try:

                        # Скворцов
                        if (max_profit - profit) > float(form['deltaP']):
                            is_running = False

                            response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                            bot.send_message(message.chat.id, text=response)

                            # Отправка команды для перезапуска стратегии
                            handle_stop(message)

                            handle_strategy_1(message)

                            return

                    except Exception as e:
                        bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                while is_running:
                    metka = None
                    delta = int(r.check_market_price() - r.check_last_order_price())
                    if delta > form['ints']['int_8']:
                        r.delete_all_orders()
                        # r.create_order_8()
                        r.create_order_9()
                        order_price = r.check_last_order_price()
                        # r.create_order_1()
                        # r.create_order_3()
                        # r.create_order_4()
                        if message:
                            bot.send_message(message.chat.id,
                                             text=f"delta={delta} --->\n" \
                                                  f"Выполнил order8-9 пок. {order_price}\n" \
                                                  f"НеВыставил ордера 1")
                        break
                    elif delta < -form['ints']['int_9']:
                        metka = r.check_market_price()
                        if message:
                            bot.send_message(message.chat.id, f"delta={delta} --->\n" \
                                                              f"Выставил метку по цене {metka}")
                            # Сквроцов
                            current_balance = r.calculate_total_balance()
                            profit = round(current_balance - enter_balance, 3)
                            max_profit = profit if profit >= max_profit else max_profit

                            # Скворцов
                            try:

                                # Скворцов
                                if (max_profit - profit) > float(form['deltaP']):
                                    is_running = False

                                    response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"
                                    bot.send_message(message.chat.id, text=response)
                                    # Отправка команды для перезапуска стратегии
                                    handle_stop(message)

                                    handle_strategy_1(message)

                                    return

                            except Exception as e:
                                bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        break
                    else:
                        if message:
                            bot.send_message(message.chat.id, f"delta={delta} ---> hold")
                            # Сквроцов
                            current_balance = r.calculate_total_balance()
                            profit = round(current_balance - enter_balance, 3)
                            max_profit = profit if profit >= max_profit else max_profit

                            # Скворцов
                            try:

                                # Скворцов
                                if (max_profit - profit) > float(form['deltaP']):
                                    is_running = False

                                    response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"
                                    bot.send_message(message.chat.id, text=response)
                                    # Отправка команды для перезапуска стратегии
                                    handle_stop(message)

                                    handle_strategy_1(message)

                                    return

                            except Exception as e:
                                bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        time.sleep(sleep_time)
                time.sleep(sleep_time)

            else:
                current_balance = r.calculate_total_balance()
                profit = round(current_balance - enter_balance, 3)
                max_profit = profit if profit >= max_profit else max_profit
                if message:
                    bot.send_message(message.chat.id, f"--Нахожусь в Блоке 4--\n" \
                                                      f"--LO_price={metka}--\n" \
                                                      f"--profit={profit} USDC, max={max_profit} USDC--")

                    # Скворцов
                    try:

                        # Скворцов
                        if (max_profit - profit) > float(form['deltaP']):
                            is_running = False

                            response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                            bot.send_message(message.chat.id, text=response)

                            # Отправка команды для перезапуска стратегии
                            handle_stop(message)

                            handle_strategy_1(message)

                            return

                    except Exception as e:
                        bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")
                while is_running:
                    delta = int(r.check_market_price() - metka)
                    if delta > form['ints']['int_7']:
                        r.delete_all_orders()
                        # r.create_order_7()
                        r.create_order_9()
                        order_price = r.check_last_order_price()
                        # r.create_order_1()
                        # r.create_order_3()
                        # r.create_order_4()
                        metka = None
                        if message:
                            bot.send_message(message.chat.id,
                                             text=f"Закрыл все ордера - delete open orders\n" \
                                                  f"delta={delta} --->\n" \
                                                  f"Выполнил order7-9 пок. {order_price}\n" \
                                                  f"НеВыставил ордера 1" \
                                                  f"Обнулил значение метки")
                            # Сквроцов
                            current_balance = r.calculate_total_balance()
                            profit = round(current_balance - enter_balance, 3)
                            max_profit = profit if profit >= max_profit else max_profit

                            # Скворцов
                            try:

                                # Скворцов
                                if (max_profit - profit) > float(form['deltaP']):
                                    is_running = False

                                    response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"
                                    bot.send_message(message.chat.id, text=response)
                                    # Отправка команды для перезапуска стратегии
                                    handle_stop(message)

                                    handle_strategy_1(message)

                                    return

                            except Exception as e:
                                bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        break
                    elif delta < -form['ints']['int_10']:
                        metka = r.check_market_price()
                        if message:
                            bot.send_message(message.chat.id, f"delta={delta} --->\n" \
                                                              f"Выставил метку по цене {metka}")
                            # Сквроцов
                            current_balance = r.calculate_total_balance()
                            profit = round(current_balance - enter_balance, 3)
                            max_profit = profit if profit >= max_profit else max_profit

                            # Скворцов
                            try:

                                # Скворцов
                                if (max_profit - profit) > float(form['deltaP']):
                                    is_running = False

                                    response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"
                                    bot.send_message(message.chat.id, text=response)
                                    # Отправка команды для перезапуска стратегии
                                    handle_stop(message)

                                    handle_strategy_1(message)

                                    return

                            except Exception as e:
                                bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        break
                    else:
                        if message:
                            bot.send_message(message.chat.id, f"delta={delta} ---> hold")
                            # Сквроцов
                            current_balance = r.calculate_total_balance()
                            profit = round(current_balance - enter_balance, 3)
                            max_profit = profit if profit >= max_profit else max_profit

                            # Скворцов
                            try:

                                # Скворцов
                                if (max_profit - profit) > float(form['deltaP']):
                                    is_running = False

                                    response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"
                                    bot.send_message(message.chat.id, text=response)
                                    # Отправка команды для перезапуска стратегии
                                    handle_stop(message)

                                    handle_strategy_1(message)

                                    return

                            except Exception as e:
                                bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        time.sleep(sleep_time)
                time.sleep(sleep_time)


@bot.message_handler(func=lambda message: message.text == "Стратегия 2(market)")
def handle_strategy_2(message):
    # обработка двойного нажатия кнопки
    global is_running
    if is_running:
        response = f"Стратегия уже выполняется.\n" \
                   f"Дождитесь выполнения стратегии."
        bot.send_message(message.chat.id, text=response)
    else:
        is_running = True

        # t0 - block0(подготовка)
        enter_balance = round(r.calculate_total_balance(), 4)
        max_profit = None
        response = f"--Подготовка--\n" \
                   f"--Начальный баланс {enter_balance} USDC"
        bot.send_message(message.chat.id, text=response)

        r.delete_all_orders()
        # r.create_order_11()
        # r.create_order_9()
        response = f"Закрыл все ордера - delete open orders.\n" \
            #          f"Выполнил order_11 прод. - продал все btc.\n"
        bot.send_message(message.chat.id, text=response)
        time.sleep(sleep_time)

        # t1 - block1
        current_balance = r.calculate_total_balance()
        profit = round(current_balance - enter_balance, 3)
        max_profit = round(profit, 3)
        lo_price = r.check_last_order_price()
        bot.send_message(message.chat.id, f"--Нахожусь в Блоке 1--\n" \
                                          f"--LO_price={lo_price}--\n" \
                                          f"--profit={profit} USDC, max={max_profit} USDC--")

        # Скворцов
        try:

            # Скворцов
            if (max_profit - profit) > float(form['deltaP']):
                is_running = False

                response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"
                bot.send_message(message.chat.id, text=response)
                # Отправка команды для перезапуска стратегии
                handle_stop(message)

                handle_strategy_1(message)

                return

        except Exception as e:
            bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")
        # r.create_order_enter_1()
        r.create_order_9()
        # r.create_order_1()
        order_price = r.check_last_order_price()
        # r.create_order_3()
        # r.create_order_4()
        bot.send_message(message.chat.id, f"Выполнил enter1-9 пок. {order_price}\n" \
                                          f"неВыставил ордера 1")

        time.sleep(sleep_time)

        # t2 - blocks2,3,4
        metka = None
        side = None
        decision = None
        while is_running:
            if metka is None:
                side = r.check_last_order_side()
                lo_price = r.check_last_order_price()
                if side == 'Buy':
                    decision = 'Блок2'
                    bot.send_message(message.chat.id, f"Last Order = {side} по {lo_price} --->\n" \
                                                      f"Перехожу в {decision}")
                else:
                    decision = 'Блок3'
                    bot.send_message(message.chat.id, f"Last Order = {side} по {lo_price} --->\n" \
                                                      f"Перехожу в {decision}")
            else:
                side = 'metka'
                decision = 'Блок4'
                bot.send_message(message.chat.id, f"Last Order = {side} по {metka} --->\n" \
                                                  f"Перехожу в {decision}")

            if side == 'Buy':
                current_balance = r.calculate_total_balance()
                profit = round(current_balance - enter_balance, 3)
                max_profit = profit if profit >= max_profit else max_profit
                lo_price = r.check_last_order_price()
                bot.send_message(message.chat.id, f"--Нахожусь в Блоке 2 --\n" \
                                                  f"--LO_price={lo_price}--\n" \
                                                  f"--profit={profit} USDC, max={max_profit} USDC--")
                # Скворцов
                try:
                    # Скворцов
                    if (max_profit - profit) > float(form['deltaP']):
                        is_running = False

                        response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                        bot.send_message(message.chat.id, text=response)

                        # Отправка команды для перезапуска стратегии
                        handle_stop(message)

                        handle_strategy_1(message)

                        return

                except Exception as e:
                    bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                while is_running:
                    delta = int(r.check_market_price() - r.check_last_order_price())
                    try:
                        order_5_is_active = r.check_orders()['name'].str.contains('order5').any()
                    except Exception:
                        order_5_is_active = False
                    # if delta < 0:
                    if delta < form['ints']['int_3']:
                        r.delete_all_orders()
                        # session.place_order(category = 'spot', symbol=form['symbol'], isLeverage = form['isLeverage'], orderType = "Market", side = 'Sell', qty = btc_amnt, marketUnit = 'baseCoin')
                        # r.create_order_9()
                        r.create_order_10()
                        bot.send_message(message.chat.id,
                                         text=f"Закрыл все ордера - delete open orders.\n" \
                                              f"delta={delta} --->\n" \
                                              f"Выполнил order101 прод.")
                        # Сквроцов
                        current_balance = r.calculate_total_balance()
                        profit = round(current_balance - enter_balance, 3)
                        max_profit = profit if profit >= max_profit else max_profit

                        # Скворцов
                        try:

                            # Скворцов
                            if (max_profit - profit) > float(form['deltaP']):
                                is_running = False

                                response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"
                                bot.send_message(message.chat.id, text=response)
                                # Отправка команды для перезапуска стратегии
                                handle_stop(message)

                                handle_strategy_1(message)

                                return

                        except Exception as e:
                            bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")
                        break
                    elif order_5_is_active == False:
                        r.delete_all_orders()  # - александр попросил закомментить
                        r.create_order_3()
                        r.create_order_5()
                        bot.send_message(message.chat.id, f"delta={delta} и order5={order_5_is_active} --->\n" \
                                                          f"Выполнил order7 пок. и выставил order5 прод. ордер1 прод")
                        # Сквроцов
                        current_balance = r.calculate_total_balance()
                        profit = round(current_balance - enter_balance, 3)
                        max_profit = profit if profit >= max_profit else max_profit

                        # Скворцов
                        try:

                            # Скворцов
                            if (max_profit - profit) > float(form['deltaP']):
                                is_running = False

                                response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                                bot.send_message(message.chat.id, text=response)

                                # Отправка команды для перезапуска стратегии
                                handle_stop(message)

                                handle_strategy_1(message)

                                return

                        except Exception as e:
                            bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")
                        break
                    else:
                        if delta >= form['ints']['int_4']:
                            r.create_order_4()
                            bot.send_message(message.chat.id, f"delta={delta}. Выполнил order4")
                            # Сквроцов
                            current_balance = r.calculate_total_balance()
                            profit = round(current_balance - enter_balance, 3)
                            max_profit = profit if profit >= max_profit else max_profit

                            # Скворцов
                            try:

                                # Скворцов
                                if (max_profit - profit) > float(form['deltaP']):
                                    is_running = False

                                    response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"
                                    bot.send_message(message.chat.id, text=response)
                                    # Отправка команды для перезапуска стратегии
                                    handle_stop(message)

                                    handle_strategy_1(message)

                                    return

                            except Exception as e:
                                bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                            break
                        else:
                            bot.send_message(message.chat.id,
                                             f"delta={delta} и order5={order_5_is_active} ---> hold order1")
                            # Скворцов
                            if order_5_is_active:
                                try:
                                    if delta > form['ints']['int_1']:
                                        r.delete_all_orders()
                                        r.create_order_1()
                                        r.create_order_5()
                                        bot.send_message(message.chat.id, "Удалил ордера и созадл ордер 1 и 5")
                                    else:
                                        bot.send_message(message.chat.id, "Делаю STOP - Стратегия 2")
                                        handle_stop(message)
                                        handle_strategy_2(message)
                                        return
                                except Exception as e:
                                    bot.send_message(message.chat.id,
                                                     f"Произошла непредвиденная ошибка во второй правке: {e}")
                            # Сквроцов
                            current_balance = r.calculate_total_balance()
                            profit = round(current_balance - enter_balance, 3)
                            max_profit = profit if profit >= max_profit else max_profit

                            # Скворцов 111111
                            try:

                                # Скворцов
                                if (max_profit - profit) > float(form['deltaP']):
                                    is_running = False

                                    response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"
                                    bot.send_message(message.chat.id, text=response)
                                    # Отправка команды для перезапуска стратегии
                                    handle_stop(message)

                                    handle_strategy_1(message)

                                    return

                            except Exception as e:
                                bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")
                            # 1111111

                        time.sleep(sleep_time)
                time.sleep(sleep_time)

            elif side == 'Sell':
                current_balance = r.calculate_total_balance()
                profit = round(current_balance - enter_balance, 3)
                max_profit = profit if profit >= max_profit else max_profit
                lo_price = r.check_last_order_price()
                bot.send_message(message.chat.id, f"--Нахожусь в Блоке 3--\n" \
                                                  f"--LO_price={lo_price}--\n" \
                                                  f"--profit={profit} USDC, max={max_profit} USDC--")

                r.delete_all_orders()
                bot.send_message(message.chat.id, "Закрыл все ордера - delete open orders")
                # Скворцов
                try:

                    # Скворцов
                    if (max_profit - profit) > float(form['deltaP']):
                        is_running = False

                        response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                        bot.send_message(message.chat.id, text=response)

                        # Отправка команды для перезапуска стратегии
                        handle_stop(message)

                        handle_strategy_1(message)

                        return

                except Exception as e:
                    bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")
                while is_running:
                    metka = None
                    delta = int(r.check_market_price() - r.check_last_order_price())
                    if delta > form['ints']['int_8']:
                        r.delete_all_orders()
                        # r.create_order_8()
                        r.create_order_9()
                        order_price = r.check_last_order_price()
                        # r.create_order_1()
                        # r.create_order_3()
                        # r.create_order_4()
                        bot.send_message(message.chat.id,
                                         text=f"delta={delta} --->\n" \
                                              f"Выполнил order8-9 пок. {order_price}\n" \
                                              f"неВыставил ордера 1")
                        # Сквроцов
                        current_balance = r.calculate_total_balance()
                        profit = round(current_balance - enter_balance, 3)
                        max_profit = profit if profit >= max_profit else max_profit

                        # Скворцов
                        try:

                            # Скворцов
                            if (max_profit - profit) > float(form['deltaP']):
                                is_running = False

                                response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                                bot.send_message(message.chat.id, text=response)

                                # Отправка команды для перезапуска стратегии
                                handle_stop(message)

                                handle_strategy_1(message)

                                return

                        except Exception as e:
                            bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")
                        break
                    elif delta < -form['ints']['int_9']:
                        metka = r.check_market_price()
                        bot.send_message(message.chat.id, f"delta={delta} --->\n" \
                                                          f"Выставил метку по цене {metka}")
                        # Сквроцов
                        current_balance = r.calculate_total_balance()
                        profit = round(current_balance - enter_balance, 3)
                        max_profit = profit if profit >= max_profit else max_profit

                        # Скворцов
                        try:

                            # Скворцов
                            if (max_profit - profit) > float(form['deltaP']):
                                is_running = False

                                response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                                bot.send_message(message.chat.id, text=response)

                                # Отправка команды для перезапуска стратегии
                                handle_stop(message)

                                handle_strategy_1(message)

                                return

                        except Exception as e:
                            bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        break
                    else:
                        bot.send_message(message.chat.id, f"delta={delta} ---> hold")
                        # Сквроцов
                        current_balance = r.calculate_total_balance()
                        profit = round(current_balance - enter_balance, 3)
                        max_profit = profit if profit >= max_profit else max_profit

                        # Скворцов
                        try:

                            # Скворцов
                            if (max_profit - profit) > float(form['deltaP']):
                                is_running = False

                                response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                                bot.send_message(message.chat.id, text=response)

                                # Отправка команды для перезапуска стратегии
                                handle_stop(message)

                                handle_strategy_1(message)

                                return

                        except Exception as e:
                            bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        time.sleep(sleep_time)
                time.sleep(sleep_time)

            else:
                current_balance = r.calculate_total_balance()
                profit = round(current_balance - enter_balance, 3)
                max_profit = profit if profit >= max_profit else max_profit
                bot.send_message(message.chat.id, f"--Нахожусь в Блоке 4--\n" \
                                                  f"--LO_price={metka}--\n" \
                                                  f"--profit={profit} USDC, max={max_profit} USDC--")
                # Скворцов
                try:

                    # Скворцов
                    if (max_profit - profit) > float(form['deltaP']):
                        is_running = False

                        response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                        bot.send_message(message.chat.id, text=response)

                        # Отправка команды для перезапуска стратегии
                        handle_stop(message)

                        handle_strategy_1(message)

                        return

                except Exception as e:
                    bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                while is_running:
                    delta = int(r.check_market_price() - metka)
                    if delta > form['ints']['int_7']:
                        r.delete_all_orders()
                        # r.create_order_7()
                        r.create_order_9()
                        order_price = r.check_last_order_price()
                        # r.create_order_1()
                        # r.create_order_3()
                        # r.create_order_4()
                        metka = None
                        bot.send_message(message.chat.id,
                                         text=f"Закрыл все ордера - delete open orders\n" \
                                              f"delta={delta} --->\n" \
                                              f"Выполнил order7 пок. {order_price}\n" \
                                              f"Выставил ордера 1" \
                                              f"Обнулил значение метки")
                        # Сквроцов
                        current_balance = r.calculate_total_balance()
                        profit = round(current_balance - enter_balance, 3)
                        max_profit = profit if profit >= max_profit else max_profit

                        # Скворцов
                        try:

                            # Скворцов
                            if (max_profit - profit) > float(form['deltaP']):
                                is_running = False

                                response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                                bot.send_message(message.chat.id, text=response)

                                # Отправка команды для перезапуска стратегии
                                handle_stop(message)

                                handle_strategy_1(message)

                                return

                        except Exception as e:
                            bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        break
                    elif delta < -form['ints']['int_10']:
                        metka = r.check_market_price()
                        bot.send_message(message.chat.id, f"delta={delta} --->\n" \
                                                          f"Выставил метку по цене {metka}")
                        # Сквроцов
                        current_balance = r.calculate_total_balance()
                        profit = round(current_balance - enter_balance, 3)
                        max_profit = profit if profit >= max_profit else max_profit

                        # Скворцов
                        try:

                            # Скворцов
                            if (max_profit - profit) > float(form['deltaP']):
                                is_running = False

                                response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                                bot.send_message(message.chat.id, text=response)

                                # Отправка команды для перезапуска стратегии
                                handle_stop(message)

                                handle_strategy_1(message)

                                return

                        except Exception as e:
                            bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        break
                    else:
                        bot.send_message(message.chat.id, f"delta={delta} ---> hold")
                        # Сквроцов
                        current_balance = r.calculate_total_balance()
                        profit = round(current_balance - enter_balance, 3)
                        max_profit = profit if profit >= max_profit else max_profit

                        # Скворцов
                        try:

                            # Скворцов
                            if (max_profit - profit) > float(form['deltaP']):
                                is_running = False

                                response = f"({max_profit} - {profit}) = {round(max_profit - profit, 3)} USDC - Делаю STOP - Стратегия 1"

                                bot.send_message(message.chat.id, text=response)

                                # Отправка команды для перезапуска стратегии
                                handle_stop(message)

                                handle_strategy_1(message)

                                return

                        except Exception as e:
                            bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")

                        time.sleep(sleep_time)
                time.sleep(sleep_time)


@bot.message_handler(func=lambda message: message.text == "Купить value_1")
def handle_buy_value_1(message):
    try:
        r.delete_all_orders()
        # r.create_order_8()
        r.create_order_9()
        # r.create_order_1()
        # r.create_order_3()
        # r.create_order_4()
        bot.send_message(message.chat.id, text='Купил value_1')
    except Exception:
        bot.send_message(message.chat.id, "Недостаточный объем usdc на балансе")


@bot.message_handler(func=lambda message: message.text == "Продать value_1")
def handle_sell_value_1(message):
    try:
        r.create_order_10()
        bot.send_message(message.chat.id, "Продал value_1")
    except Exception:
        bot.send_message(message.chat.id, "Объем на балансе < value_1")


@bot.message_handler(func=lambda message: message.text == "Баланс")
def handle_balance(message):
    try:
        token1_balance, token2_balance, total_balance = r.calculate_balance()
        response = f"Ваш текущий баланс:\n" \
                   f"USDC: {token1_balance:.5f}\n" \
                   f"BTC: {token2_balance:.8f}\n" \
                   f"Общий баланс: {total_balance:.7f} USDC"
        bot.send_message(message.chat.id, text=response)
    except:
        bot.send_message(message.chat.id, "Баланс не может быть посчитан")


@bot.message_handler(func=lambda message: message.text == "Интервалы")
def handle_ints(message):
    try:
        response = f"Интервалы: \n {form['ints']}"
        bot.send_message(message.chat.id, text=response)
    except Exception:
        bot.send_message(message.chat.id, "Не заданы интревалы")

    try:
        response = f"Триггеры: \n {form['int_triggers']}"
        bot.send_message(message.chat.id, text=response)
    except Exception:
        bot.send_message(message.chat.id, "Не заданы триггерные интревалы")


@bot.message_handler(func=lambda message: message.text == "Текущие Ордера")
def handle_orders(message):
    try:
        fr_ = r.check_orders().head(7)
        response = tabulate(fr_, headers='keys', tablefmt='pretty')
        bot.send_message(message.chat.id, text=response)
    except Exception:
        response = "Нет открытых ордеров"
        bot.send_message(message.chat.id, text=response)


@bot.message_handler(func=lambda message: message.text == "Last Trades")
def handle_trades(message):
    try:
        trades = r.check_trades().head(10)
        response = tabulate(trades, headers='keys', tablefmt='pretty')
        bot.send_message(message.chat.id, text=response)
    except Exception:
        response = "Отсутствует история торговли"
        bot.send_message(message.chat.id, text=response)


@bot.message_handler(func=lambda message: message.text == "ВКЛ СЧЕТЧИК")
def handle_vkl(message):
    global is_running
    if is_running:
        bot.send_message(message.chat.id, "Счетчик уже включен")
    else:
        is_running = True
        bot.send_message(message.chat.id, "Включил счетчик")


@bot.message_handler(func=lambda message: message.text == "ВЫКЛ СЧЕТЧИК(del_orders)")
def handle_vikl(message):
    r.delete_all_orders()
    global is_running
    if is_running == False:
        bot.send_message(message.chat.id, "Счетчик уже выключен")
    else:
        is_running = False
        bot.send_message(message.chat.id, "Выключил счетчик")


@bot.message_handler(func=lambda message: message.text == "STOP")
def handle_stop(message):
    global is_running
    is_running = False
    r.delete_all_orders()
    try:
        r.create_order_11()
        token1_balance, token2_balance, total_balance = r.calculate_balance()
        if message:
            bot.send_message(message.chat.id,
                             text=f"--Робот удален. Все btc проданы.--\n" \
                                  f"--Общий баланс: {total_balance:.7f} USDC--")
    except InvalidRequestError:
        response = f"Не могу продать btc, не хватает баланса.\n" \
                   f"Обратить внимание."
        if message:
            bot.send_message(message.chat.id, text=response)


# Запуск бота
while True:
    try:
        bot.polling(none_stop=True, restart_on_change=True, path_to_watch='../restart.txt')
    except Exception as e:
        print(e)
        time.sleep(15)
