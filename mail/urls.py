from django.urls import path
from . import views

urlpatterns = [
    # Я открываю главную страницу почтового клиента.
    path("", views.mailbox, name="mailbox"),

    # Я описываю маршруты авторизации и сессии.
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("current_user/", views.current_user, name="current_user"),

    # Я описываю маршруты работы с письмами.
    path("send/", views.send_email, name="send_email"),
    path("emails/<str:folder>/", views.get_emails, name="get_emails"),
    path("email/<int:email_id>/", views.read_email, name="read_email"),
    path("email/<int:email_id>/move/", views.move_email, name="move_email"),
    path(
        "email/<int:email_id>/delete/",
        views.delete_email,
        name="delete_email",
    ),
]
