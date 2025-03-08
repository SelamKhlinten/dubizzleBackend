from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from core.user.models import User  

class Conversation(models.Model):
    sender = models.ForeignKey(User, related_name='sent_conversations', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_conversations', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        unique_together = ('sender', 'receiver')  # Ensures only one conversation exists between two users.

    def clean(self):
        """Prevents a user from starting a conversation with themselves."""
        if self.sender == self.receiver:
            raise ValidationError("A user cannot start a conversation with themselves.")

    def __str__(self):
        return f"Conversation between {self.sender.first_name} and {self.receiver.first_name}"

    def get_receiver(self, sender):
        """Given a sender, return the other participant in the conversation."""
        return self.receiver if sender == self.sender else self.sender if sender == self.receiver else None

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # Read receipt

    class Meta:
        ordering = ['created_at']  # Ensure messages are ordered chronologically

    def __str__(self):
        return f"Message from {self.sender.first_name} at {self.created_at}"

    def get_receiver(self):
        """Returns the receiver of the message."""
        return self.conversation.get_receiver(self.sender)
