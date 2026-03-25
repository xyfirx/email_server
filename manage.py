#!/usr/bin/env python
"""Командный файл для запуска административных команд Django."""
import os
import sys


def main():
    """Запускает административные команды проекта."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            'Не удалось импортировать Django. Проверьте, что пакет '
            'установлен и виртуальное окружение активировано.'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
