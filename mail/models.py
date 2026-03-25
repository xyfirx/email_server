from django.db import models
from django.contrib.auth.models import User


# Я описываю допустимые значения папок.
FOLDER_CHOICES = [
    ('inbox', 'Входящие'),
    ('sent', 'Отправленные'),
    ('draft', 'Черновики'),
    ('archive', 'Архив'),
    ('trash', 'Корзина'),
]


class Email(models.Model):
    # Я храню отправителя письма.
    sender: models.ForeignKey = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # при удаление отправителя письма удаляются
        related_name='sent_emails',
    )

    # Я храню получателя; у черновика он может отсутствовать.
    receiver: models.ForeignKey = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_emails',
    )

    # Я храню адрес получателя как строку username@tmal.ru.
    receiver_email: models.CharField = models.CharField(
        max_length=50,
        blank=True,
        default='',
    )

    # Я храню тему; у черновика она может быть пустой.
    subject: models.CharField = models.CharField(
        max_length=100,
        blank=True,
        default='',
    )

    # Я храню текст письма.
    body: models.TextField = models.TextField(
        blank=True,
        default='',
    )

    is_read: models.BooleanField = models.BooleanField(
        default=False,
    )

    # Я храню папку, в которой лежит письмо.
    folder: models.CharField = models.CharField(
        max_length=10,
        choices=FOLDER_CHOICES,
        default='inbox',
    )

    # Я храню вложение, если пользователь его прикрепил.
    attachment: models.FileField = models.FileField(
        upload_to='attachments/',
        null=True,
        blank=True,
    )

    created_at: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.subject or '(без темы)'


class UserPreference(models.Model):
    # Я храню пользователя, которому принадлежат настройки.
    user: models.OneToOneField = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='mail_preference',
    )

    def __str__(self):
        return f'Настройки {self.user.username}'
