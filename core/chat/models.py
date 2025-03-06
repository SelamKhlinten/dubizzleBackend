from django.conf import settings
from django.db import models

class Conversation(models.Model):
    users = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f"Conversation between {', '.join([user.username for user in self.users.all()])}"

class Chat(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField() 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.first_name} at {self.created_at}"
