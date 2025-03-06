# models.py
from django.db import models
from core.user.models import User

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # The user who will receive the notification
    message = models.CharField(max_length=255)  # Message content
    is_read = models.BooleanField(default=False)  # Whether the notification has been read
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when the notification was created

    def __str__(self):
        return f"Notification for {self.user.first_name}"
