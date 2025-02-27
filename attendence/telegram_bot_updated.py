import telebot
from django.conf import settings
from .models import TelegramGroup2, SendMessage
import logging
import os
from datetime import datetime
from attendence.secret import TOKEN

log_file = 'telegram_bot.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Single bot instance
_bot = None

def get_bot():
    global _bot
    if _bot is None:
        try:
            _bot = telebot.TeleBot(TOKEN)
            logger.info("Bot initialized successfully with token")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {str(e)}")
            raise
    return _bot

bot = get_bot()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.reply_to(message, "Привет! Я бот для отправки уведомлений. Используйте следующие команды:\n"
                         "/addgroup - Добавить текущую группу в список рассылки\n"
                         "/removegroup - Удалить текущую группу из списка рассылки\n"
                         "/status - Проверить статус текущей группы")
        logger.info(f"Welcome message sent to chat {message.chat.id}")
    except Exception as e:
        logger.error(f"Error in send_welcome: {e}")
        bot.reply_to(message, "Произошла ошибка при обработке команды")

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
                logger.info(f"New group added: {message.chat.title} (ID: {message.chat.id})")
            else:
                if not group.is_active:
                    group.is_active = True
                    group.save()
                    bot.reply_to(message, "Группа восстановлена в списке рассылки! ✅")
                    logger.info(f"Group reactivated: {message.chat.title} (ID: {message.chat.id})")
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
                logger.info(f"Group removed: {message.chat.title} (ID: {message.chat.id})")
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
                logger.info(f"Status checked for group: {message.chat.title} (ID: {message.chat.id})")
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
    Send notification to selected groups or all active groups
    message_obj: SendMessage instance
    """
    try:
        logger.info(f"Starting to send notification for message ID: {message_obj.id}")
        
        if message_obj.all_groups:
            target_groups = TelegramGroup2.objects.filter(is_active=True)
            logger.info(f"Sending to all active groups. Found {target_groups.count()} groups")
        else:
            target_groups = message_obj.groups.filter(is_active=True)
            logger.info(f"Sending to selected groups. Found {target_groups.count()} groups")

        if not target_groups.exists():
            logger.warning("No target groups found!")
            message_obj.status = 'failed'
            message_obj.error_message = 'No target groups found'
            message_obj.save()
            return

        success = True
        error_message = None
        
        for group in target_groups:
            try:
                logger.info(f"Attempting to send message to group: {group.group_name} (ID: {group.group_id})")
                
                if message_obj.image:
                    logger.info(f"Sending image: {message_obj.image.path}")
                    with open(message_obj.image.path, 'rb') as photo:
                        bot.send_photo(
                            group.group_id,
                            photo,
                            caption=message_obj.message if message_obj.message else None
                        )
                        logger.info("Image sent successfully")
                elif message_obj.message:
                    logger.info("Sending text message")
                    bot.send_message(group.group_id, message_obj.message)
                    logger.info("Text message sent successfully")
                
            except Exception as e:
                logger.error(f"Error sending message to group {group.group_name}: {str(e)}")
                success = False
                error_message = str(e)
                continue

        # Обновляем статус сообщения
        status = 'sent' if success else 'failed'
        logger.info(f"Updating message status to: {status}")
        message_obj.status = status
        message_obj.error_message = error_message
        message_obj.sent_at = datetime.now()
        message_obj.save()
        logger.info("Message status updated successfully")

    except Exception as e:
        logger.error(f"Critical error in send_notification: {str(e)}")
        message_obj.status = 'failed'
        message_obj.error_message = str(e)
        message_obj.save()
        raise

def start_bot():
    """
    Start the bot in a separate thread
    """
    try:
        bot = get_bot()
        logger.info("Starting bot polling...")
        # Запускаем бота в режиме polling
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise

def test_bot_connection():
    """
    Test if the bot is properly connected and can receive updates
    """
    try:
        bot_info = bot.get_me()
        logger.info(f"Bot connection test successful! Bot info: {bot_info.first_name} (@{bot_info.username})")
        return True
    except Exception as e:
        logger.error(f"Bot connection test failed: {str(e)}")
        return False

def test_send_message(chat_id):
    """
    Test sending a message to a specific chat
    """
    try:
        message = "🤖 Тестовое сообщение от бота"
        sent_message = bot.send_message(chat_id, message)
        logger.info(f"Test message sent successfully to chat {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send test message: {str(e)}")
        return False

def check_bot_status():
    try:
        bot = get_bot()
        bot_info = bot.get_me()
        active_groups = TelegramGroup2.objects.filter(is_active=True)
        
        status = {
            "bot_connected": True,
            "bot_username": f"@{bot_info.username}",
            "bot_name": bot_info.first_name,
            "active_groups_count": active_groups.count(),
            "active_groups": [f"{group.group_name} (ID: {group.group_id})" for group in active_groups],
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return status
    except Exception as e:
        logger.error(f"Error in check_bot_status: {e}")
        return {"bot_connected": False, "error": str(e)}

# Инициализируем бота только при явном вызове, убираем автозапуск
bot = get_bot()

if __name__ == '__main__':
    logger.info("This module should not be run directly. Use 'python manage.py runbot' instead.")
