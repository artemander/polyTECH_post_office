import telebot
import requests
from telebot import types


bot = telebot.TeleBot('7855850689:AAEiGsETbIhfsQOAra60Ctg2s7i2Adsqqbc')


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Добро пожаловать! Пожалуйста, введите ваш пароль, полученный на терминале.")
    bot.register_next_step_handler(message, check_password)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == '/check_in':
        checkReg = requests.get('http://localhost/postdon/hs/tickets/v1/check_registered', headers={'username': message.from_user.username})
        # print(checkReg.status_code)
        if checkReg.status_code == 200:
            result = requests.get('http://localhost/postdon/hs/tickets/v1/all_actions')
            # print(result.status_code)
            if result.status_code == 200:
                keyboard = types.InlineKeyboardMarkup()
                for line in result.text.split('\n'):
                    try:
                        action, act_id = line.split('_')
                        keyboard.add(types.InlineKeyboardButton(text=action, callback_data='%1' + act_id))
                    except:
                        pass
                bot.send_message(message.from_user.id, text="Выберите услугу: ", reply_markup=keyboard)
        elif checkReg.status_code == 201:
            bot.send_message(message.chat.id, "Вы не зарегистрированы")


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data.startswith('%1'):
        keyboard = types.InlineKeyboardMarkup()
        previous = None
        for x in range(8, 18):
            if previous is None:
                previous = types.InlineKeyboardButton(text=f'{("0" + str(x))[-2:]}:XX', callback_data='%2' + call.data[2:] + '&' + str(x))
            else:
                keyboard.add(previous, types.InlineKeyboardButton(text=f'{("0" + str(x))[-2:]}:XX', callback_data='%2' + call.data[2:] + '&' + str(x)))
                previous = None
        bot.send_message(call.message.chat.id, 'Выберите час, на который хотите записаться', reply_markup=keyboard)
    elif call.data.startswith('%2'):
        keyboard = types.InlineKeyboardMarkup()
        for x in range(0, 60, 15):
            keyboard.add(
                types.InlineKeyboardButton(text=("0" + str(x))[-2:], callback_data='%3' + call.data[2:] + '&' + str(x)))
        bot.send_message(call.message.chat.id, 'Выберите минуту, на которую хотите записаться', reply_markup=keyboard)
    elif call.data.startswith('%3'):
        dta = call.data.split('&')
        action = dta.pop(0)[2:]
        time = ' '.join(dta)
        result = requests.post('http://localhost/postdon/hs/tickets/v1/check_time',
                               data=str({'act': action, 'time': time, 'username': call.message.chat.username}))
        # print(result.status_code)
        if result.status_code == 200 or result.status_code == 201:
            bot.send_message(call.message.chat.id, "Вот ваш талон")
            with open('ticket.pdf', "wb+") as file:
                file.write(result.content)
            with open('ticket.pdf', "rb") as file:
                bot.send_document(call.message.chat.id, document=file)
        elif result.status_code == 213:
            bot.send_message(call.message.chat.id, result.text)
        else:
            bot.send_message(call.message.chat.id, "Ошибка подключения к серверу")


def check_password(message):
    result = requests.get('http://localhost/postdon/hs/registration/v1/newuser', headers={'num': message.text, 'username': message.from_user.username})
    if result.status_code == 201:
        bot.send_message(message.from_user.id, "Номер введён неправильно")
        bot.register_next_step_handler(message, check_password)
    elif result.status_code == 200:
        bot.send_message(message.from_user.id, "Спасибо за регистрацию")


bot.polling()