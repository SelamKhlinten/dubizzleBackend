from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model to return basic user info."""
    
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]

class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model with sender and receiver details."""
    
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "sender", "receiver", "created_at"]

class StartConversationSerializer(serializers.Serializer):
    """Serializer for starting a new conversation."""
    
    receiver_id = serializers.IntegerField()

    def validate_receiver_id(self, value):
        """Ensure the receiver exists and is not the sender."""
        sender = self.context["request"].user
        if sender.id == value:
            raise serializers.ValidationError("You cannot start a conversation with yourself.")
        
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Receiver does not exist.")
        
        return value

    def create(self, validated_data):
        """Create or get an existing one-to-one conversation."""
        sender = self.context["request"].user
        receiver = User.objects.get(id=validated_data["receiver_id"])
        
        conversation, created = Conversation.objects.get_or_create(
            sender=sender, receiver=receiver
        )
        
        return conversation

class ChatSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'receiver', 'content', 'created_at', 'is_read']

    def get_receiver(self, obj):
        """Get the receiver of the message."""
        return UserSerializer(obj.get_receiver()).data

    def create(self, validated_data):
        """Ensure the sender is the logged-in user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['sender'] = request.user
        return super().create(validated_data)
