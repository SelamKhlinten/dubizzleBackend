from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import Conversation, Chat
from .serializers import ConversationSerializer, ChatSerializer, StartConversationSerializer

class ConversationViewSet(viewsets.ViewSet):
    """ViewSet for managing one-on-one conversations."""
    
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Get all conversations for the authenticated user."""
        user = request.user
        conversations = Conversation.objects.filter(Q(sender=user) | Q(receiver=user))
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """Start a new conversation or return an existing one."""
        serializer = StartConversationSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            conversation = serializer.save()
            return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """Get a specific conversation by ID."""
        user = request.user
        try:
            conversation = Conversation.objects.get(Q(id=pk) & (Q(sender=user) | Q(receiver=user)))
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ChatViewSet(viewsets.ModelViewSet):
    """ViewSet for managing chat messages."""
    
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter messages to only those in conversations involving the user."""
        return Chat.objects.filter(
            Q(conversation__sender=self.request.user) | Q(conversation__receiver=self.request.user)
        )

    def perform_create(self, serializer):
        """Ensure sender is the authenticated user."""
        sender = self.request.user
        conversation = serializer.validated_data['conversation']

        # Ensure the sender is part of the conversation
        if sender != conversation.sender and sender != conversation.receiver:
            return Response({"error": "You are not a participant in this conversation."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer.save(sender=sender)

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """Mark messages in a conversation as read."""
        user = request.user
        try:
            chat = Chat.objects.get(id=pk, conversation__in=Conversation.objects.filter(Q(sender=user) | Q(receiver=user)))
            chat.is_read = True
            chat.save()
            return Response({"message": "Message marked as read."}, status=status.HTTP_200_OK)
        except Chat.DoesNotExist:
            return Response({"error": "Message not found or access denied."}, status=status.HTTP_404_NOT_FOUND)
