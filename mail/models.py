from django.db import models
from django.contrib.auth.models import User


class Email(models.Model):

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_emails"
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_emails"
    )

    subject = models.CharField(max_length=255)

    body = models.TextField()

    is_read = models.BooleanField(default=False)

    folder = models.CharField(
        max_length=20,
        default="inbox"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject