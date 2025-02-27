from django.core.management.base import BaseCommand
from attendence.telegram_bot_updated import start_bot, check_bot_status, test_bot_connection, logger

class Command(BaseCommand):
    help = 'Запускает Telegram бота'

    def handle(self, *args, **kwargs):
        self.stdout.write('Запуск Telegram бота...')
        
        try:
            # Проверяем статус бота
            bot_status = check_bot_status()
            if bot_status["bot_connected"]:
                self.stdout.write(self.style.SUCCESS(f"Бот подключен как {bot_status['bot_username']}"))
                self.stdout.write(f"Активных групп: {bot_status['active_groups_count']}")
            else:
                self.stdout.write(self.style.ERROR("Бот не подключен!"))
                return

            # Тестируем соединение
            if test_bot_connection():
                self.stdout.write(self.style.SUCCESS("Тест соединения успешен"))
            else:
                self.stdout.write(self.style.ERROR("Тест соединения не удался!"))
                return

            # Запускаем бота
            start_bot()
            self.stdout.write(self.style.SUCCESS('Бот успешно запущен!'))
            
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}")
            self.stdout.write(self.style.ERROR(f'Ошибка запуска бота: {e}'))
