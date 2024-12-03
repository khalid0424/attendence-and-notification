import telebot
from secret import BOT_TOKEN



bot = telebot.TeleBot(BOT_TOKEN)

def send_message_to_telegram(chat_id, text=None, image_path=None):
    try:
        if image_path:
            with open(image_path, 'rb') as image_file:
                bot.send_photo(chat_id, image_file, caption=text)
        elif text:
            bot.send_message(chat_id, text)
    except Exception as e:
        print(f"Error: {e}")
