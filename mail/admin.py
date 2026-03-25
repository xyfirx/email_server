from typing import cast

from django.contrib import admin
from django.db.models import Field

from .models import Email

Email._meta.verbose_name = 'Письмо'
Email._meta.verbose_name_plural = 'Письма'

cast(Field, Email._meta.get_field('folder')).verbose_name = 'Папка'
cast(Field, Email._meta.get_field('is_read')).verbose_name = 'Прочитано'
cast(Field, Email._meta.get_field('created_at')).verbose_name = (
    'Дата создания'
)

admin.site.site_header = 'Администрирование Tmal'
admin.site.site_title = 'Админ-панель Tmal'
admin.site.index_title = 'Управление системой'


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sender_ru',
        'receiver_email_ru',
        'subject_ru',
        'folder_ru',
        'is_read_ru',
        'created_at_ru',
    )
    list_filter = ('folder', 'is_read', 'created_at')
    search_fields = ('subject', 'sender__username', 'receiver_email')

    @admin.display(description='Отправитель')
    def sender_ru(self, obj):
        return obj.sender

    @admin.display(description='Почта получателя')
    def receiver_email_ru(self, obj):
        return obj.receiver_email

    @admin.display(description='Тема')
    def subject_ru(self, obj):
        return obj.subject or '(без темы)'

    @admin.display(description='Папка')
    def folder_ru(self, obj):
        return obj.get_folder_display()

    @admin.display(description='Прочитано')
    def is_read_ru(self, obj):
        return 'Да' if obj.is_read else 'Нет'

    @admin.display(description='Дата создания')
    def created_at_ru(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
