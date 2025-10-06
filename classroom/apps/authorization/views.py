from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Notification
from .serializers import NotificationSerializer, NotificationListSerializer, NotificationMarkReadSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_read", "notification_type", "created_at"]

    def get_queryset(self):
        # Ensure users can only see their own notifications
        return self.queryset.filter(recipient=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return NotificationListSerializer
        # For retrieve, create, update, delete actions, use the detailed serializer
        return NotificationSerializer

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        # Ensure the user is the recipient of the notification
        if notification.recipient != request.user:
            raise permissions.PermissionDenied("You can only mark your own notifications as read")
        notification.mark_as_read()
        return Response({"status": "notification marked as read"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def mark_as_unread(self, request, pk=None):
        notification = self.get_object()
        # Ensure the user is the recipient of the notification
        if notification.recipient != request.user:
            raise permissions.PermissionDenied("You can only mark your own notifications as unread")
        notification.mark_as_unread()
        return Response({"status": "notification marked as unread"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        self.get_queryset().filter(recipient=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
        return Response({"status": "all notifications marked as read"}, status=status.HTTP_200_OK)

    # Existing unread action, modified to use get_queryset
    @action(detail=False, methods=["get"])
    def unread(self, request):
        queryset = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
