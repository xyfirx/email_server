from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import json
from .models import Email
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as django_login, logout as django_logout


def home(request):
    return HttpResponse("Сервер почты работает")


def mailbox(request):
    # render frontend interface
    return render(request, "mail/mailbox.html")


def user_list(request):
    # return list of users for dropdowns
    users = User.objects.all().values("id", "username")
    return JsonResponse(list(users), safe=False)


@csrf_exempt
def register_user(request):
    # simple registration API (no auth)
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        email = data.get("email", "")
        password = data.get("password")
        if not username or not password:
            return JsonResponse({"message": "Имя и пароль обязательны"}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({"message": "Пользователь существует"}, status=400)
        user = User.objects.create_user(username=username, email=email, password=password)
        return JsonResponse({"message": "Пользователь создан", "id": user.id, "username": user.username})
    return JsonResponse({"message": "Только POST"}, status=405)


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        user = authenticate(username=username, password=password)
        if user is not None:
            django_login(request, user)
            return JsonResponse({"message": "Вход выполнен"})
        return JsonResponse({"message": "Неверные учетные данные"}, status=400)
    return JsonResponse({"message": "Только POST"}, status=405)


@csrf_exempt
def logout_user(request):
    django_logout(request)
    return JsonResponse({"message": "Выход"})


def current_user(request):
    if request.user.is_authenticated:
        return JsonResponse({"id": request.user.id, "username": request.user.username})
    return JsonResponse({}, status=204)


@csrf_exempt
def send_email(request):

    if request.method == "POST":

        data = json.loads(request.body)

        # prefer logged in user as sender if available
        if request.user.is_authenticated:
            sender = request.user
        else:
            sender = User.objects.get(id=data["sender"])
        receiver = User.objects.get(id=data["receiver"])

        email = Email.objects.create(
            sender=sender,
            receiver=receiver,
            subject=data["subject"],
            body=data["body"],
            folder="sent"
        )

        Email.objects.create(
            sender=sender,
            receiver=receiver,
            subject=data["subject"],
            body=data["body"],
            folder="inbox"
        )

        return JsonResponse({"message": "Письмо отправлено"})
    

@csrf_exempt
def move_email(request, email_id):

    if request.method == "PUT":

        data = json.loads(request.body)

        email = Email.objects.get(id=email_id)
        # ensure current user can modify this email
        if request.user.is_authenticated:
            if request.user != email.sender and request.user != email.receiver:
                return JsonResponse({"message": "Недоступно"}, status=403)

        email.folder = data["folder"]
        email.save()

        return JsonResponse({"message": "Письмо перемещено"})


def get_emails(request, folder):

    emails = Email.objects.filter(folder=folder)
    # restrict to logged-in user's messages if authenticated
    if request.user.is_authenticated:
        if folder == 'inbox':
            emails = emails.filter(receiver=request.user)
        elif folder == 'sent':
            emails = emails.filter(sender=request.user)
        else:
            # trash/archive show any where user is sender or receiver
            emails = emails.filter(sender=request.user) | emails.filter(receiver=request.user)

    data = []

    for email in emails:
        data.append({
            "id": email.id,
            "sender": email.sender.username,
            "receiver": email.receiver.username,
            "subject": email.subject,
            "is_read": email.is_read,
            "date": email.created_at
        })

    return JsonResponse(data, safe=False)


def read_email(request, email_id):

    email = Email.objects.get(id=email_id)

    # ensure user has access
    if request.user.is_authenticated:
        if request.user != email.sender and request.user != email.receiver:
            return JsonResponse({"message": "Недоступно"}, status=403)

    email.is_read = True
    email.save()

    data = {
        "sender": email.sender.username,
        "receiver": email.receiver.username,
        "subject": email.subject,
        "body": email.body,
        "date": email.created_at,
        "is_read": email.is_read
    }

    return JsonResponse(data)


def delete_email(request, email_id):

    email = Email.objects.get(id=email_id)
    # restrict
    if request.user.is_authenticated:
        if request.user != email.sender and request.user != email.receiver:
            return JsonResponse({"message": "Недоступно"}, status=403)

    email.delete()

    return JsonResponse({"message": "Удалено"})