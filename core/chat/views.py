# views.py
from rest_framework import viewsets
from .models import Conversation, Chat
from .serializers import Conversation, ChatSerializer

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = Conversation

    def get_queryset(self):
        return Conversation.objects.filter(users=self.request.user)  # Only show conversations the user is part of

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    def perform_create(self, serializer):
        # Link the message to a specific conversation
        conversation = Conversation.objects.get(id=self.request.data['conversation_id'])
        serializer.save(conversation=conversation, sender=self.request.user)
