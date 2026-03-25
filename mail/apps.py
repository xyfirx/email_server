from django.apps import AppConfig


# Класс конфигурации приложения "Почта".
class MailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mail'
    verbose_name = 'Почта'
