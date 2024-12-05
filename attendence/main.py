import telebot
from telebot.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from attendence.secret import API_BOT
from attendence.contex import *
from attendence.models import Student, Class, TelegramGroup
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

def register_commands():
    commands = [
        {'command': 'start', 'description': 'Начать работу с ботом'},
        {'command': 'addgroup', 'description': 'Добавить группу для уведомлений'},
        {'command': 'removegroup', 'description': 'Удалить группу из уведомлений'},
        {'command': 'linkclass', 'description': 'Привязать группу к классу'}
    ]
    bot.set_my_commands(commands)

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
    print(f"Получено сообщение: {message.text}")
    command = message.text.split('@')[0] if '@' in message.text else message.text
    
    if command == '/addgroup':
        print("Начинаем обработку команды addgroup")
        try:
            if message.chat.type != 'group' and message.chat.type != 'supergroup':
                bot.reply_to(message, "❌ Эта команда работает только в групповых чатах!")
                return

            group_id = str(message.chat.id)
            group_name = message.chat.title if hasattr(message.chat, 'title') else str(message.chat.id)
            
            print(f"Добавление группы: {group_name} (ID: {group_id})")
            existing_group = TelegramGroup.objects.filter(group_id=group_id).first()
            if existing_group:
                if existing_group.is_active:
                    bot.reply_to(message, "✅ Эта группа уже добавлена в систему уведомлений!")
                else:
                    existing_group.is_active = True
                    existing_group.save()
                    bot.reply_to(message, "✅ Группа успешно активирована!")
                return

            new_group = TelegramGroup.objects.create(
                group_id=group_id,
                group_name=group_name,
                is_active=True
            )
            print(f"Группа создана: {new_group}")
            bot.reply_to(message, "✅ Группа успешно добавлена в систему уведомлений!")
            
        except Exception as e:
            print(f"Ошибка при добавлении группы: {str(e)}")
            import traceback
            print(traceback.format_exc())
            bot.reply_to(message, f"❌ Произошла ошибка: {str(e)}")

    elif command == "Я пришел!":
        is_user_exist = get_student(message.chat.id)
        if not is_user_exist:
            bot.send_message(message.chat.id, "Вы уже отметились сегодня!")
            return
                
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        location_button = KeyboardButton("Отправить свое местоположение", request_location=True)
        markup.add(location_button)
        bot.send_message(message.chat.id, "Пожалуйста, отправьте ваше местоположение для подтверждения.", reply_markup=markup)
    
    elif command == "Я сегодня не приду":
        is_user_exist = get_student3(message.chat.id)
        if is_user_exist:
            bot.send_message(message.chat.id, "Скажите причину, почему вы не пришли сегодня?")
            bot.register_next_step_handler(message, prichina)
        else:
            bot.send_message(message.chat.id, "Вы уже отметились сегодня!")
    
    elif command == "Я сегодня опоздаю!":
        is_user_exist = get_student4(message.chat.id)
        if is_user_exist:
            bot.send_message(message.chat.id, "Скажите причину, почему вы опоздали?")
            bot.register_next_step_handler(message, late_reason)
        else:
            bot.send_message(message.chat.id, "Вы уже отметились сегодня!")
    
    elif command == "Я ухожу домой!":
        if update_out(message.chat.id):
            bot.send_message(message.chat.id, "До завтра и не опаздывайте, пожалуйста!")
        else:
            bot.send_message(message.chat.id, "Вы еще не отметились как пришедший или уже ушли домой!")

    elif command == '/removegroup':
        try:
            if message.chat.type != 'group' and message.chat.type != 'supergroup':
                bot.reply_to(message, "❌ Эта команда работает только в групповых чатах!")
                return

            group_id = str(message.chat.id)
            group = TelegramGroup.objects.filter(group_id=group_id).first()
            
            if not group:
                bot.reply_to(message, "❌ Эта группа не найдена в системе уведомлений!")
                return
                
            group.is_active = False
            group.save()
            bot.reply_to(message, "✅ Группа успешно удалена из системы уведомлений!")
            
        except Exception as e:
            print(f"Ошибка при удалении группы: {str(e)}")
            bot.reply_to(message, f"❌ Произошла ошибка: {str(e)}")

    elif command == '/linkclass':
        try:
            if message.chat.type != 'group' and message.chat.type != 'supergroup':
                bot.reply_to(message, "❌ Эта команда работает только в групповых чатах!")
                return

            args = message.text.split()
            if len(args) < 2:
                bot.reply_to(message, "❌ Пожалуйста, укажите ID класса после команды.\nПример: /linkclass 1")
                return

            class_id = args[1]
            try:
                class_obj = Class.objects.get(id=class_id)
            except Class.DoesNotExist:
                bot.reply_to(message, f"❌ Класс с ID {class_id} не найден!")
                return

            group_id = str(message.chat.id)
            group = TelegramGroup.objects.filter(group_id=group_id).first()
            
            if not group:
                bot.reply_to(message, "❌ Сначала добавьте группу в систему командой /addgroup!")
                return

            group.class_id = class_obj
            group.save()
            bot.reply_to(message, f"✅ Группа успешно привязана к классу {class_obj.name}!")
            
        except Exception as e:
            print(f"Ошибка при привязке класса: {str(e)}")
            bot.reply_to(message, f"❌ Произошла ошибка: {str(e)}")

@bot.message_handler(content_types=["location"])
def handle_location(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = KeyboardButton("Я пришел!")
    btn2 = KeyboardButton("Я сегодня не приду")
    btn4 = KeyboardButton("Я сегодня опоздаю!")
    btn5 = KeyboardButton("Я ухожу домой!")
    markup.row(btn1, btn2, btn5, btn4)
    
    if not message.location or not message.location.latitude or not message.location.longitude:
        bot.send_message(message.chat.id, "Не удалось получить ваше местоположение. Попробуйте еще раз.", reply_markup=markup)
        return

    user_lat = message.location.latitude
    user_lon = message.location.longitude
    distance = calculate_distance(user_lat, user_lon, Soft_lat, Soft_lon)

    if distance <= 50:
        if save_students_come(message):
            bot.send_message(message.chat.id, "Отлично! Вы успешно отметились.", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Вы уже отмечены сегодня.", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f"Вы находитесь слишком далеко от Soft Club (расстояние: {distance:.0f} метров)", reply_markup=markup)

@bot.message_handler()
def ask_location(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    location_button = KeyboardButton("Отправить свое местоположение", request_location=True)
    markup.add(location_button)
    bot.send_message(message.chat.id, "Пожалуйста, отправьте ваше местоположение.", reply_markup=markup)

def send_group_notification(student, status, reason):
    try:
        print(f"\n=== Отправка уведомления ===")
        print(f"Студент: {student.f_name} {student.l_name}")
        print(f"Статус: {status}")
        print(f"Причина: {reason}")

        all_groups = TelegramGroup.objects.filter(is_active=True)
        print(f"\nВсе активные группы:")
        for group in all_groups:
            print(f"- {group.group_name} (ID: {group.group_id})")

        student_classes = student.class_id.all()
        print(f"\nКлассы студента:")
        for class_obj in student_classes:
            print(f"- {class_obj.name}")

        groups = TelegramGroup.objects.filter(
            class_id__in=student_classes,
            is_active=True
        )
        print(f"\nНайденные группы для классов студента:")
        for group in groups:
            print(f"- {group.group_name} (ID: {group.group_id})")

        if not groups.exists():
            print("❌ Нет активных групп для этого студента")
            groups = all_groups
            print("Используем все активные группы для тестирования")

        student_name = f"{student.f_name} {student.l_name}" if student.l_name else student.f_name
        
        if status == "absent":
            message = f"❌ Студент {student_name} сегодня не придет\nПричина: {reason}\nГруппа: {student.class_id.all().first()}"
        elif status == "late":
            # for i in student.class_id.first()
            message = f"⚠️ Студент {student_name} сегодня опоздает\nПричина: {reason}\nГруппа: {student.class_id.all().first()}"
        
        print(f"\nПодготовленное сообщение:")
        print(message)

        for group in groups:
            try:
                print(f"\nОтправка в группу {group.group_name}...")
                bot.send_message(group.group_id, message)
                print(f"✅ Успешно отправлено в группу {group.group_name}")
            except Exception as e:
                print(f"❌ Ошибка при отправке в группу {group.group_name}: {str(e)}")

    except Exception as e:
        print(f"❌ Общая ошибка при отправке уведомлений: {str(e)}")
        import traceback
        print(f"Подробности ошибки:\n{traceback.format_exc()}")

def prichina(message):
    student = Student.objects.get(telegram_id=message.chat.id)
    save_students_notcome(message, message.text)
    send_group_notification(student, "absent", message.text)
    bot.send_message(message.chat.id, "Спасибо, что написали причину, по которой не сможете прийти!")

def late_reason(message):
    student = Student.objects.get(telegram_id=message.chat.id)
    save_students_late(message, message.text)
    send_group_notification(student, "late", message.text)
    bot.send_message(message.chat.id, "Спасибо за объяснили почему опоздали, что бы больше такого не повторалось!")

def new_username(message):
    username = message.text
    save_students_come2(message, username) 
    bot.send_message(message.chat.id, "Спасибо, теперь вы можете использовать бот :)") 

def add_group(message):
    group = message.text
    update_user(message.chat.id, group)
    bot.send_message(message.chat.id, "Спасибо, теперь вы можете использовать бот :)") 


if __name__ == "__main__":
    print("Бот запускается...")
    register_commands()
    print("Команды зарегистрированы")
    bot.polling(none_stop=True)
else:
    print("Регистрация команд...")
    register_commands()
    print("Команды зарегистрированы")
    bot.polling(none_stop=True)
