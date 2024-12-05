from django.apps import AppConfig
from django.utils import timezone
# apps.py
from django.apps import AppConfig

class AttendenceConfig(AppConfig):
    name = 'attendence'

    def ready(self):
        import attendence.signals  # Подключаем сигналы

class AttendenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendence'
    verbose_name = 'Система учета посещаемости'

    def ready(self):
        try:
            from .signals import mark_students_absent
            from django.core.cache import cache
            
            # Инициализируем кэш при запуске
            today = timezone.localtime().date()
            cache_key = f'marked_absent_{today}'
            if not cache.get(cache_key):
                mark_students_absent()
        except Exception as e:
            print(f"Ошибка в AttendenceConfig.ready(): {str(e)}")
