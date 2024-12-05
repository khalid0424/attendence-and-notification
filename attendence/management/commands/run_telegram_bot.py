from django.core.management.base import BaseCommand
from attendence.telegram_bot_updated import bot
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запускает Telegram бота для отправки уведомлений'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Запуск Telegram бота...'))
        
        try:
            # Запускаем бота в режиме polling
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            self.stdout.write(self.style.ERROR(f'Ошибка при запуске бота: {e}'))
        finally:
            self.stdout.write(self.style.SUCCESS('Бот остановлен'))
