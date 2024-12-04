import telebot
from telebot.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from attendence.secret import API_BOT
from attendence.contex import *
from math import radians, sin, cos, sqrt, atan2

bot = telebot.TeleBot(API_BOT)

Soft_lat = 38.56401624794034
Soft_lon = 68.75892534477292

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    a = sin(delta_phi / 2)**2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

@bot.message_handler(commands=["start"])
def start_choice(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton("Я пришел!")
    btn2 = KeyboardButton("Я сегодня не приду")
    btn4 = KeyboardButton("Я сегодня опоздаю!")
    btn5 = KeyboardButton("Я ухожу домой!")
    markup.row(btn1, btn2, btn5, btn4)

    markup2 = ReplyKeyboardMarkup(resize_keyboard=True)
    group = get_groups()
    for subject_name in group:
        btn = KeyboardButton(subject_name)
        markup2.add(btn)
    
    is_user_exist = get_student1(message.chat.id)
    if is_user_exist:
        if message.chat.username:
            save_students(message)
        else:
            bot.send_message(message.chat.id, "У вас нет username, пожалуйста, введите его: ")
            bot.register_next_step_handler(message, new_username)
            
    bot.send_message(message.chat.id, "Добро пожаловать в мой бот:) Пожалуйста, выберите одну из этих кнопок!", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Я пришел!":
        is_user_exist = get_student(message.chat.id)
        if is_user_exist:
            # Check if student was late
            if handle_late_arrival(message.chat.id):
                bot.send_message(message.chat.id, "Добро пожаловать! Пожалуйста, не опаздывайте в следующий раз.")
            else:
                markup = ReplyKeyboardMarkup(resize_keyboard=True)
                location_button = KeyboardButton("Отправить свое местоположение", request_location=True)
                markup.add(location_button)
                bot.send_message(message.chat.id, "Пожалуйста, отправьте ваше местоположение.", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Вы уже отметились сегодня!")
    elif message.text == "Я сегодня не приду":
        is_user_exist = get_student3(message.chat.id)
        if is_user_exist:
            bot.send_message(message.chat.id, "Скажите причину, почему вы не пришли сегодня?")
            bot.register_next_step_handler(message, prichina)
        else:
            bot.send_message(message.chat.id, "Вы уже отметились сегодня!")
    elif message.text == "Я сегодня опоздаю!":
        is_user_exist = get_student4(message.chat.id)
        if is_user_exist:
            bot.send_message(message.chat.id, "Скажите причину, почему вы опоздали?")
            bot.register_next_step_handler(message, late_reason)
        else:
            bot.send_message(message.chat.id, "Вы уже отметились сегодня!")
    elif message.text == "Я ухожу домой!":
        if update_out(message.chat.id):
            bot.send_message(message.chat.id, "До завтра и не опаздывайте, пожалуйста!")
        else:
            bot.send_message(message.chat.id, "Вы еще не отметились как пришедший или уже ушли домой!")

@bot.message_handler(content_types=["location"])
def handle_location(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton("Я пришел!")
    btn2 = KeyboardButton("Я сегодня не приду")
    btn4 = KeyboardButton("Я сегодня опоздаю!")
    btn5 = KeyboardButton("Я ухожу домой!")
    markup.row(btn1, btn2, btn5, btn4)
    
    if not message.location or not message.location.latitude or not message.location.longitude:
        bot.send_message(message.chat.id, "Не удалось получить ваше местоположение. Попробуйте еще раз.")
        return

    user_lat = message.location.latitude
    user_lon = message.location.longitude
    distance = calculate_distance(user_lat, user_lon, Soft_lat, Soft_lon)

    if distance <= 50:
        save_students_come(message)
        bot.send_message(message.chat.id, "Молодец, что вы пришли !!", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f"Вы не находитесь в Soft Club, от вас {distance:.2f} метров до софтклаба", reply_markup=markup)

@bot.message_handler()
def ask_location(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    location_button = KeyboardButton("Отправить свое местоположение", request_location=True)
    markup.add(location_button)
    bot.send_message(message.chat.id, "Пожалуйста, отправьте ваше местоположение.", reply_markup=markup)

def prichina(message):
    save_students_notcome(message, message.text)
    bot.send_message(message.chat.id, "Спасибо, что написали причину, по которой не сможете прийти!")

def late_reason(message):
    save_students_late(message, message.text)
    bot.send_message(message.chat.id, "Спасибо за объяснение, что опоздали!")

def new_username(message):
    username = message.text
    save_students_come2(message, username) 
    bot.send_message(message.chat.id, "Спасибо, теперь вы можете использовать бот :)") 

def add_group(message):
    group = message.text
    update_user(message.chat.id, group)
    bot.send_message(message.chat.id, "Спасибо, теперь вы можете использовать бот :)") 

bot.polling(none_stop=True)
