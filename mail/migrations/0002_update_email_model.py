import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Добавляем строковый адрес получателя
        migrations.AddField(
            model_name='email',
            name='receiver_email',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        # Добавляем поле для прикреплённого файла
        migrations.AddField(
            model_name='email',
            name='attachment',
            field=models.FileField(
                blank=True, null=True, upload_to='attachments/'
            ),
        ),
        # Поле receiver теперь необязательное (для черновиков)
        migrations.AlterField(
            model_name='email',
            name='receiver',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='received_emails',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Тема может быть пустой у черновика
        migrations.AlterField(
            model_name='email',
            name='subject',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        # Тело тоже необязательное
        migrations.AlterField(
            model_name='email',
            name='body',
            field=models.TextField(blank=True, default=''),
        ),
        # Папка: уменьшаем длину и добавляем choices
        migrations.AlterField(
            model_name='email',
            name='folder',
            field=models.CharField(
                choices=[
                    ('inbox', 'Входящие'),
                    ('sent', 'Отправленные'),
                    ('draft', 'Черновики'),
                    ('trash', 'Корзина'),
                ],
                default='inbox',
                max_length=10,
            ),
        ),
    ]
