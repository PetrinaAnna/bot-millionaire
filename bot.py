import os
import redis

import telebot
from telebot import TeleBot
from telebot import types

REDIS_URL = os.environ.get('REDIS_URL')
redis_db = redis.from_url(REDIS_URL, decode_responses=True)
MAIN_STATE = 'main'
QUESTION = 'question_date'
REPLY = 'reply_date'
STOP = 'stop'
COUNT ='count'
api_url = 'https://stepik.akentev.com/api/millionaire'
correct_answer = {}
states = {}
score = { }


def add_defeats(user_id, score_num):
    if user_id in score:
        score[user_id]['defeats'] += score_num
    else:
        score[user_id] = {"victories": 0, "defeats": 1}


def add_victories(user_id, score_num):
    if user_id in score:
        score[user_id]['victories'] += score_num
    else:
        score[user_id] = {"victories": 1, "defeats": 0}


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
    elif state == STOP:
        stop(message)
    elif state == COUNT:
        count(message)


def main_handler(message):
    if message.text == '/start':
        reset_markup = types.ReplyKeyboardRemove()
        bot.send_message(message.from_user.id, 'Это бот-игра в "Кто хочет стать миллионером"',
                         reply_markup=reset_markup)
        # states[message.from_user.id] = MAIN_STATE
        save(str(message.from_user.id), MAIN_STATE)

    elif message.text == 'Задай мне вопрос':
        bot.send_message(message.from_user.id,
                         'Секундочку, только уточню некоторые детали:на вопросы какой сложности Вы хотели бы отвечать? выберите 1, 2 или 3')
        # states[message.from_user.id] = QUESTION
        save(str(message.from_user.id), QUESTION)


def question_date(message):
    if message.text == 'Задай мне вопрос' or 'Ещё!':
        import requests
        requests.get(api_url).json()
        result = requests.get(api_url).json()
        print(result)
        victory = result['answers'][0]
        # correct_answers['right'] = victory
        save('right', victory)
        print(victory)

        import random
        random.shuffle(result['answers'])
        text = result['question']

        for answer in result['answers']:
            text = text + '\n' + answer

        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, )
        buttons = []

        for answer in result['answers']:
            buttons.append(types.KeyboardButton(answer))
        markup.add(*buttons)

        bot.send_message(message.from_user.id, text, reply_markup=markup)
        # states[message.from_user.id] = REPLY
        save(str(message.from_user.id), REPLY)

    # else:
    # bot.send_message(message.from_user.id, 'Я тебя не понял')
    # states[message.from_user.id] = MAIN_STATE
    # save(str(message.from_user.id), MAIN_STATE)

def reply_date(message):
    # if message.text in victories['right']:
    correct_answer = load('right')
    if message.text == correct_answer:
        add_victories(message.from_user.id, 1)
        reset_markup = types.ReplyKeyboardRemove()
        bot.send_message(message.from_user.id, 'Правильно', reply_markup=reset_markup)
        # states[message.from_user.id] = QUESTION
        save(str(message.from_user.id), QUESTION)
    elif message.text != correct_answer:
        add_defeats(message.from_user.id, 1)
        reset_markup = types.ReplyKeyboardRemove()
        bot.send_message(message.from_user.id, 'Не правильно! Закончить игру?', reply_markup=reset_markup)
        # states[message.from_user.id] = MAIN_STATE
        save(str(message.from_user.id), STOP)

def stop(message):
    if message.text == 'Нет':
        bot.send_message(message.from_user.id, 'Тогда продолжим')
        save(str(message.from_user.id), QUESTION)
    elif message.text == 'Да':
        bot.send_message(message.from_user.id, 'Показать Ваш счет?')
        save(str(message.from_user.id), COUNT)

def count(message):
     if message.text == 'Да':
        bot.send_message(message.from_user.id,
                                 'Побед: ' + str(score[message.from_user.id]['victories']) + ' Поражений: ' + str(score[message.from_user.id]['defeats']))
              # states[message.from_user.id] = MAIN_STATE
        save(str(message.from_user.id), MAIN_STATE)
     elif message.text == 'Нет':
      # states[message.from_user.id] = MAIN_STATE
        save(str(message.from_user.id), MAIN_STATE)


bot.polling()