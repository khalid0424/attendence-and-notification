from django.core.management.base import BaseCommand
import telebot
from attendence.main import bot  # Импортируйте объект вашего бота

class Command(BaseCommand):
    help = 'Запуск Telegram-бота'
    def handle(self, *args, **kwargs):
        bot.infinity_polling()  # Запуск бота
