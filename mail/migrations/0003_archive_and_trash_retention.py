import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0002_update_email_model'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='email',
            name='trash_delete_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='email',
            name='folder',
            field=models.CharField(
                choices=[
                    ('inbox', 'Входящие'),
                    ('sent', 'Отправленные'),
                    ('draft', 'Черновики'),
                    ('archive', 'Архив'),
                    ('trash', 'Корзина'),
                ],
                default='inbox',
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'trash_retention_days',
                    models.PositiveSmallIntegerField(
                        choices=[(5, '5 дней'), (10, '10 дней'),
                                 (15, '15 дней')],
                        default=10,
                    ),
                ),
                (
                    'user',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='mail_preference',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
