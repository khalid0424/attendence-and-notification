import telebot
from django.conf import settings
from .models import TelegramGroup2, SendMessage
import logging
import os
from datetime import datetime
from attendence.secret import TOKEN

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот для отправки уведомлений. Используйте следующие команды:\n"
                         "/addgroup - Добавить текущую группу в список рассылки\n"
                         "/removegroup - Удалить текущую группу из списка рассылки\n"
                         "/status - Проверить статус текущей группы")

@bot.message_handler(commands=['addgroup'])
def add_group(message):
    if message.chat.type in ['group', 'supergroup']:
        try:
            group, created = TelegramGroup2.objects.get_or_create(
                group_id=str(message.chat.id),
                defaults={'group_name': message.chat.title, 'is_active': True}
            )
            if created:
                bot.reply_to(message, "Группа успешно добавлена в список рассылки! ✅")
            else:
                if not group.is_active:
                    group.is_active = True
                    group.save()
                    bot.reply_to(message, "Группа восстановлена в списке рассылки! ✅")
                else:
                    bot.reply_to(message, "Эта группа уже в списке рассылки! ℹ️")
        except Exception as e:
            logger.error(f"Error adding group: {e}")
            bot.reply_to(message, "Произошла ошибка при добавлении группы ❌")
    else:
        bot.reply_to(message, "Эта команда работает только в группах! ⚠️")

@bot.message_handler(commands=['removegroup'])
def remove_group(message):
    if message.chat.type in ['group', 'supergroup']:
        try:
            group = TelegramGroup2.objects.filter(group_id=str(message.chat.id)).first()
            if group:
                group.is_active = False
                group.save()
                bot.reply_to(message, "Группа удалена из списка рассылки! ✅")
            else:
                bot.reply_to(message, "Эта группа не найдена в списке рассылки! ℹ️")
        except Exception as e:
            logger.error(f"Error removing group: {e}")
            bot.reply_to(message, "Произошла ошибка при удалении группы ❌")
    else:
        bot.reply_to(message, "Эта команда работает только в группах! ⚠️")

@bot.message_handler(commands=['status'])
def group_status(message):
    if message.chat.type in ['group', 'supergroup']:
        try:
            group = TelegramGroup2.objects.filter(group_id=str(message.chat.id)).first()
            if group:
                status = "активна ✅" if group.is_active else "неактивна ❌"
                bot.reply_to(message, f"Статус группы: {status}\n"
                                    f"Название: {group.group_name}\n"
                                    f"ID: {group.group_id}")
            else:
                bot.reply_to(message, "Эта группа не зарегистрирована в системе! ⚠️")
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            bot.reply_to(message, "Произошла ошибка при проверке статуса ❌")
    else:
        bot.reply_to(message, "Эта команда работает только в группах! ⚠️")

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_member(message):
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id == bot.get_me().id:
                bot.send_message(message.chat.id, 
                               "Спасибо за добавление! Используйте /addgroup чтобы добавить эту группу в список рассылки.")

def send_notification(message_obj):
    """
    Send notification to all active groups
    message_obj: SendMessage instance
    """
    groups = TelegramGroup2.objects.filter(is_active=True)
    
    for group in groups:
        try:
            if message_obj.image:
                with open(message_obj.image.path, 'rb') as photo:
                    bot.send_photo(
                        group.group_id,
                        photo,
                        caption=message_obj.message
                    )
            else:
                bot.send_message(group.group_id, message_obj.message)
        except Exception as e:
            logger.error(f"Error sending message to group {group.group_id}: {e}")

def start_bot():
    """
    Start the bot in a separate thread
    """
    try:
        logger.info("Starting bot polling...")
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
