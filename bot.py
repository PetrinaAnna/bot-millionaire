import telebot
from telebot import TeleBot

import os
import redis

REDIS_URL = os.environ.get('REDIS_URL')
redis_db = redis.from_url(REDIS_URL, decode_responses=True)

MAIN_STATE = 'main'
QUESTION = 'question_date'
REPLY = 'reply_date'

api_url = 'https://stepik.akentev.com/api/millionaire'
victories = {}
states = {}
# calls = {'victories': 0, 'defeats': 0}


def save(key, value):
    if REDIS_URL:
        redis_db = redis.from_url(REDIS_URL, decode_responses=True)
        redis_db.set(key, value)
    else:
        states[key] = value


def load(key):
    if REDIS_URL:
        redis_db = redis.from_url(REDIS_URL, decode_responses=True)
        return redis_db.get(key) or MAIN_STATE
    else:
        return states.get(key) or MAIN_STATE


token = os.environ["TELEGRAM_TOKEN"]

bot: TeleBot = telebot.TeleBot(token)


@bot.message_handler(func=lambda message: True)
def dispatcher(message):
    print(states)

    user_id = message.from_user.id
    # state = states.get(user_id, MAIN_STATE)
    state = load(str(message.from_user.id))

    # # save('state:{user_id}'.format(message.from_user.id), MAIN_STATE)
    # # load('state:{user_id}'.format(message.from_user.id))
    # save(str(message.from_user.id), MAIN_STATE)
    # user_state = str(message.from_user.id)

    print('current state', user_id, state)

    if state == MAIN_STATE:
        main_handler(message)

    elif state == QUESTION:
        question_date(message)

    elif state == REPLY:
        reply_date(message)


def main_handler(message):
    if message.text == '/start':
        bot.send_message(message.from_user.id, 'Это бот-игра в "Кто хочет стать миллионером"')
        # states[message.from_user.id] = MAIN_STATE
        save(str(message.from_user.id), MAIN_STATE)

    elif message.text == 'Привет':
        bot.send_message(message.from_user.id, 'Ну привет')
        # states[message.from_user.id] = QUESTION
        save(str(message.from_user.id), QUESTION)


def question_date(message):
    if message.text == 'Спроси меня вопрос':

        import requests
        requests.get(api_url).json()
        result = requests.get(api_url).json()
        print(result)
        victory = result['answers'][0]
        victories['right'] = victory
        print(victories)

        import random
        random.shuffle(result['answers'])
        text = result['question']
        for answer in result['answers']:
            text = text + '\n' + answer
        bot.send_message(message.from_user.id, text)
        # states[message.from_user.id] = REPLY
        save(str(message.from_user.id), REPLY)
    else:
        bot.reply_to(message, 'Я тебя не понял')
        # states[message.from_user.id] = MAIN_STATE
        save(str(message.from_user.id), MAIN_STATE)


def reply_date(message, user_win=0, user_loss=0):
    if message.text in victories['right']:
        bot.send_message(message.from_user.id, 'Правильно')
        # states[message.from_user.id] = QUESTION
        save(str(message.from_user.id), QUESTION)

        user_win = load(str(message.from_user.id) + '-wins')

        if user_win >= 0 and user_win != 'NONE':
            user_win = user_win + 1
        else:
            user_win = 0

        save(str(message.from_user.id) + '-wins', user_win)

    else:
        bot.send_message(message.from_user.id, 'Не правильно')
        # states[message.from_user.id] = MAIN_STATE
        save(str(message.from_user.id), MAIN_STATE)

        user_loss = load(str(message.from_user.id) + '-losses')

        if user_loss >= 0 and user_loss != 'NONE':
            user_loss = user_loss + 1
        else:
            user_loss = 0

        save(str(message.from_user.id) + '-loses', user_loss)
        bot.send_message(message.from_user.id,
                         'Вы ответили правильно на: ' + user_win + ' вопросов и неправильно на: ' + user_loss)


bot.polling()
