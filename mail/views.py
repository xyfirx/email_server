"""HTTP-обработчики почтового приложения и вспомогательные функции API."""

import json
import os

from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_http_methods,
)

from .models import (
    Email,
    FOLDER_CHOICES,
)

ALLOWED_FOLDERS = {code for code, _ in FOLDER_CHOICES}


def _error(message, status=400):
    """Возвращает JSON-ошибку с текстом и HTTP-статусом."""
    return JsonResponse({'message': message}, status=status)


def _require_auth(request):
    """Проверяет авторизацию и возвращает ошибку при её отсутствии."""
    if not request.user.is_authenticated:
        return _error('Требуется авторизация', status=401)
    return None


def _parse_json(request):
    """Безопасно разбирает JSON-тело запроса и возвращает словарь или None."""
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return None


def _get_user_email_or_error(email_id, user):
    """Находит письмо по ID и проверяет права доступа текущего пользователя."""
    try:
        email = Email.objects.get(id=email_id)
    except Email.DoesNotExist:
        return None, _error('Письмо не найдено', status=404)

    if user != email.sender and user != email.receiver:
        return None, _error('Нет доступа', status=403)

    return email, None


def _create_email_copy(
    *,
    sender,
    receiver_email,
    subject,
    body,
    folder,
    attachment,
    receiver=None,
):
    """Создаёт запись письма в указанной папке для отправителя/получателя."""
    Email.objects.create(
        sender=sender,
        receiver=receiver,
        receiver_email=receiver_email,
        subject=subject,
        body=body,
        folder=folder,
        attachment=attachment,
    )


def mailbox(request):
    """Отдаёт HTML-страницу интерфейса почтового клиента."""
    return render(request, 'mail/mailbox.html')


@csrf_exempt
@require_POST
def register_user(request):
    """Регистрирует пользователя, выполняет вход и возвращает профиль."""
    data = _parse_json(request)
    if data is None:
        return _error('Некорректный JSON', status=400)

    username = (data.get('username') or '').strip()
    password = data.get('password')

    if not username or not password:
        return _error('Имя и пароль обязательны', status=400)

    if User.objects.filter(username=username).exists():
        return _error('Пользователь уже существует', status=400)

    email_address = f'{username}@tmal.ru'
    if User.objects.filter(email=email_address).exists():
        return _error('Адрес уже занят', status=400)

    user = User.objects.create_user(
        username=username,
        email=email_address,
        password=password,
    )
    auth_login(request, user)

    return JsonResponse({
        'message': 'Регистрация успешна',
        'id': user.id,
        'username': user.username,
        'email': user.email,
    })


@csrf_exempt
@require_POST
def login_user(request):
    """Проверяет учётные данные и возвращает данные пользователя."""
    data = _parse_json(request)
    if data is None:
        return _error('Некорректный JSON', status=400)

    username = data.get('username')
    password = data.get('password')
    user = authenticate(request, username=username, password=password)

    if user is None:
        return _error('Неверные учётные данные', status=400)

    auth_login(request, user)
    return JsonResponse({
        'message': 'Вход выполнен',
        'id': user.id,
        'username': user.username,
        'email': user.email,
    })


@csrf_exempt
@require_POST
def logout_user(request):
    """Завершает текущую пользовательскую сессию."""
    auth_logout(request)
    return JsonResponse({'message': 'Выход выполнен'})


def current_user(request):
    """Возвращает текущего пользователя или флаг неавторизованности."""
    if request.user.is_authenticated:
        return JsonResponse({
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        })
    return JsonResponse({'authenticated': False})


@csrf_exempt
@require_POST
def send_email(request):
    """Сохраняет черновик или отправляет письмо в inbox/sent."""
    err = _require_auth(request)
    if err:
        return err

    to_email = (request.POST.get('to_email') or '').strip()
    subject = (request.POST.get('subject') or '').strip()
    body = (request.POST.get('body') or '').strip()
    is_draft = request.POST.get('draft') == '1'
    attachment = request.FILES.get('attachment')

    if is_draft:
        _create_email_copy(
            sender=request.user,
            receiver_email=to_email,
            subject=subject,
            body=body,
            folder='draft',
            attachment=attachment,
        )
        return JsonResponse({'message': 'Черновик сохранён'}, status=201)

    if not to_email:
        return _error('Укажите адрес получателя', status=400)

    try:
        receiver = User.objects.get(email=to_email)
    except User.DoesNotExist:
        return _error(f'Пользователь {to_email} не найден', status=404)

    sender = request.user
    for folder in ('sent', 'inbox'):
        _create_email_copy(
            sender=sender,
            receiver=receiver,
            receiver_email=to_email,
            subject=subject,
            body=body,
            folder=folder,
            attachment=attachment,
        )

    return JsonResponse({'message': 'Письмо отправлено'}, status=201)


@require_GET
def get_emails(request, folder):
    """Возвращает список писем папки, доступных текущему пользователю."""
    err = _require_auth(request)
    if err:
        return err

    if folder not in ALLOWED_FOLDERS:
        return _error('Некорректная папка', status=400)

    base_query = Email.objects.filter(folder=folder)

    folder_owner_map = {
        'inbox': 'receiver',
        'sent': 'sender',
        'draft': 'sender',
    }

    owner_field = folder_owner_map.get(folder)
    if owner_field:
        emails = base_query.filter(**{owner_field: request.user})
    else:
        emails = base_query.filter(sender=request.user) | base_query.filter(
            receiver=request.user
        )

    emails = emails.order_by('-created_at')

    data = [
        {
            'id': e.id,
            'sender': e.sender.username,
            'sender_email': e.sender.email,
            'receiver_email': e.receiver_email,
            'subject': e.subject or '(без темы)',
            'body_preview': e.body[:80] if e.body else '',
            'is_read': e.is_read,
            'read_status': 'Прочитано' if e.is_read else 'Не прочитано',
            'date': e.created_at.strftime('%d.%m.%Y %H:%M'),
            'has_attachment': bool(e.attachment),
        }
        for e in emails
    ]

    return JsonResponse(data, safe=False)


@require_GET
def read_email(request, email_id):
    """Возвращает полные данные письма и отмечает входящее как прочитанное."""
    err = _require_auth(request)
    if err:
        return err

    email, err = _get_user_email_or_error(email_id, request.user)
    if err:
        return err

    if request.user == email.receiver and not email.is_read:
        email.is_read = True
        email.save(update_fields=['is_read'])

    data = {
        'id': email.id,
        'sender': email.sender.username,
        'sender_email': email.sender.email,
        'receiver_email': email.receiver_email,
        'subject': email.subject or '(без темы)',
        'body': email.body,
        'date': email.created_at.strftime('%d.%m.%Y %H:%M'),
        'is_read': email.is_read,
        'read_status': 'Прочитано' if email.is_read else 'Не прочитано',
        'folder': email.folder,
        'attachment_url': (
            email.attachment.url if email.attachment else None
        ),
        'attachment_name': (
            os.path.basename(email.attachment.name)
            if email.attachment else None
        ),
    }
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(['PUT'])
def move_email(request, email_id):
    """Перемещает письмо в целевую папку с учётом ограничений бизнес-правил."""
    err = _require_auth(request)
    if err:
        return err

    data = _parse_json(request)
    if data is None:
        return _error('Некорректный JSON', status=400)

    folder = data.get('folder')
    if folder not in ALLOWED_FOLDERS:
        return _error('Некорректная папка', status=400)

    email, err = _get_user_email_or_error(email_id, request.user)
    if err:
        return err

    if email.folder == 'sent' and folder in {'archive', 'trash'}:
        return _error(
            'Отправленные письма нельзя перемещать в архив или корзину',
            status=400,
        )

    email.folder = folder
    email.save(update_fields=['folder'])
    return JsonResponse({'message': 'Письмо перемещено'})


@csrf_exempt
@require_http_methods(['DELETE'])
def delete_email(request, email_id):
    """Удаляет письмо безвозвратно по идентификатору."""
    err = _require_auth(request)
    if err:
        return err

    email, err = _get_user_email_or_error(email_id, request.user)
    if err:
        return err

    email.delete()
    return JsonResponse({'message': 'Письмо удалено'})
