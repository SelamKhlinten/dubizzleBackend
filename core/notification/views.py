# views.py
from rest_framework import viewsets
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)  # Filter notifications for the current user

    def perform_create(self, serializer):
        # Optionally, send a notification when certain actions occur
        serializer.save(user=self.request.user)
