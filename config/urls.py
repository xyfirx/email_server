from django.contrib import admin
from django.urls import path, include
from mail.views import home

urlpatterns = [
    path('', home),
    path('mail/', include('mail.urls')),
]