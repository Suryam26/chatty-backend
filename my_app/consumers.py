import json
from uuid import UUID

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.db.models import Count

from .api.serializers import MessageSerializer, UserStatusSerializer
from .models import Conversation, Message, UserStatus

User = get_user_model()


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)


class ChatConsumer(JsonWebsocketConsumer):
    """
    This consumer is used to show user's online status,
    and send notifications.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = None
        self.conversation_name = None
        self.conversation = None

    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            return

        self.accept()
        self.conversation_name = f"{self.scope['url_route']['kwargs']['conversation_name']}"
        self.conversation, created = Conversation.objects.get_or_create(name=self.conversation_name)

        async_to_sync(self.channel_layer.group_add)(
            self.conversation_name,
            self.channel_name,
        )
        self.send_json({"type": "welcome_message", "message": "Hey there! You've successfully connected!", })

        messages = self.conversation.messages.all().order_by("-timestamp")[0:50]
        message_count = self.conversation.messages.all().count()
        self.send_json(
            {
                "type": "last_50_messages",
                "messages": MessageSerializer(messages, many=True).data,
                "has_more": message_count > 50,
            }
        )

    def disconnect(self, code):
        return super().disconnect(code)

    def receive_json(self, content, **kwargs):
        message_type = content["type"]
        if message_type == "chat_message":
            message = Message.objects.create(
                from_user=self.user,
                to_user=self.get_receiver(),
                content=content["message"],
                conversation=self.conversation
            )

            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "chat_message_echo",
                    "name": self.user.username,
                    "message": MessageSerializer(message).data,
                },
            )

            notification_group_name = self.get_receiver().username + "__notifications"
            async_to_sync(self.channel_layer.group_send)(
                notification_group_name,
                {
                    "type": "new_message_notification",
                    "name": self.user.username,
                    "message": MessageSerializer(message).data,
                },
            )

        if message_type == "typing":
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "typing",
                    "user": self.user.username,
                    "typing": content["typing"],
                },
            )
            notification_group_name = self.get_receiver().username + "__notifications"
            async_to_sync(self.channel_layer.group_send)(
                notification_group_name,
                {
                    "type": "typing_notification",
                    "name": self.user.username,
                    "typing": content["typing"],
                },
            )

        if message_type == "read_messages":
            messages_to_me = self.conversation.messages.filter(to_user=self.user)
            messages_to_me.update(read=True)

            # Update the unread message count
            unread_count = Message.objects.filter(to_user=self.user, read=False).count()
            async_to_sync(self.channel_layer.group_send)(
                self.user.username + "__notifications",
                {
                    "type": "unread_count",
                    "unread_count": unread_count,
                },
            )
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_name,
                {
                    "type": "update_read_messages",
                    "user": self.user.username,
                    "sender": self.get_receiver().username,
                },
            )

        if message_type == "delete_message":
            message_id = content["message_id"]
            message = Message.objects.get(id=message_id)
            if message.from_user == self.user:
                message.delete()
                async_to_sync(self.channel_layer.group_send)(
                    self.conversation_name,
                    {
                        "type": "delete_message",
                        "message_id": message_id,
                    },
                )
                notification_group_name = self.get_receiver().username + "__notifications"
                async_to_sync(self.channel_layer.group_send)(
                    notification_group_name,
                    {
                        "type": "delete_message",
                        "name": self.user.username,
                        "message": MessageSerializer(message).data,
                    },
                )

        return super().receive_json(content, **kwargs)

    def get_receiver(self):
        usernames = self.conversation_name.split("__")

        if usernames == usernames[::-1]:
            # Sender and receiver are the same
            return User.objects.get(username=usernames[0])

        for username in usernames:
            if username != self.user.username:
                # This is the receiver
                return User.objects.get(username=username)

    def chat_message_echo(self, event):
        self.send_json(event)

    @classmethod
    def encode_json(cls, content):
        return json.dumps(content, cls=UUIDEncoder)

    def typing(self, event):
        self.send_json(event)

    def new_message_notification(self, event):
        self.send_json(event)

    def unread_count(self, event):
        self.send_json(event)

    def update_read_messages(self, event):
        self.send_json(event)

    def delete_message(self, event):
        self.send_json(event)


class NotificationConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = None
        self.notification_group_name = None

    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            return

        self.accept()

        self.notification_group_name = self.user.username + "__notifications"
        async_to_sync(self.channel_layer.group_add)(
            self.notification_group_name,
            self.channel_name,
        )

        unread_count = Message.objects.filter(to_user=self.user, read=False).count()
        unread_count_list = Message.objects.values("from_user__username").annotate(
            count=Count("from_user__username")).filter(to_user=self.user, read=False)

        self.send_json(
            {
                "type": "unread_count",
                "unread_count": unread_count,
                "unread_count_list": list(unread_count_list)
            }
        )

    def disconnect(self, code):
        if self.user.is_authenticated:
            async_to_sync(self.channel_layer.group_discard)(
                self.notification_group_name,
                self.channel_name,
            )
        return super().disconnect(code)

    def new_message_notification(self, event):
        self.send_json(event)

    def unread_count(self, event):
        self.send_json(event)

    def typing_notification(self, event):
        self.send_json(event)

    def delete_message(self, event):
        self.send_json(event)


class UserStatusConsumer(JsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.user = None
        self.user_status_group_name = "online_users"

    def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            return

        self.accept()

        async_to_sync(self.channel_layer.group_add)(
            self.user_status_group_name,
            self.channel_name,
        )

        self.send_json({"type": "welcome_message", "message": "Hey there! You've successfully connected!", })

        user_status, created = UserStatus.objects.get_or_create(user=self.user)
        user_status.join()

        async_to_sync(self.channel_layer.group_send)(
            self.user_status_group_name,
            {
                "type": "user_status",
                "user": user_status.user.username,
                "status": UserStatusSerializer(user_status).data,
            },
        )

    def disconnect(self, code):
        if self.user.is_authenticated:
            user_status = UserStatus.objects.get(user=self.user)
            user_status.leave()

            async_to_sync(self.channel_layer.group_send)(
                self.user_status_group_name,
                {
                    "type": "user_status",
                    "user": self.user.username,
                    "status": UserStatusSerializer(user_status).data,
                },
            )

        return super().disconnect(code)

    @classmethod
    def encode_json(cls, content):
        return json.dumps(content, cls=UUIDEncoder)

    def user_status(self, event):
        self.send_json(event)
