from django.urls import path
from . import views

urlpatterns = [
    # frontend interface
    path("", views.mailbox, name="mailbox"),
    path("users/", views.user_list, name="user_list"),
    path("register/", views.register_user, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("current_user/", views.current_user, name="current_user"),

    # API endpoints
    path("send/", views.send_email),
    path("emails/<str:folder>/", views.get_emails),
    path("email/<int:email_id>/", views.read_email),
    path("email/<int:email_id>/move/", views.move_email),
    path("email/<int:email_id>/delete/", views.delete_email),
]