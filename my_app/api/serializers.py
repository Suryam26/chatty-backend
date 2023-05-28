from django.contrib.auth import get_user_model
from rest_framework import serializers

from my_app.models import Message, Conversation, UserStatus
from users.api.serializers import UserSerializer

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    from_user = serializers.SerializerMethodField()
    to_user = serializers.SerializerMethodField()
    conversation = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "from_user",
            "to_user",
            "content",
            "timestamp",
            "read",
            "is_deleted",
        )

    def get_conversation(self, obj):
        return str(obj.conversation.id)

    def get_from_user(self, obj):
        return UserSerializer(obj.from_user).data

    def get_to_user(self, obj):
        return UserSerializer(obj.to_user).data


class ConversationSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "name", "other_user", "last_message")

    def get_last_message(self, obj):
        messages = obj.messages.all().order_by("-timestamp")
        if not messages.exists():
            return None
        message = messages[0]
        return MessageSerializer(message).data

    def get_other_user(self, obj):
        usernames = obj.name.split("__")
        context = {}
        other_user = None

        if usernames == usernames[::-1]:
            # This is a conversation with myself
            other_user = self.context["user"]

        for username in usernames:
            if username != self.context["user"].username:
                # This is the other participant
                other_user = User.objects.get(username=username)

        return UserSerializer(other_user, context=context).data


class UserStatusSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()

    class Meta:
        model = UserStatus
        fields = ("id", "user", "online", "last_seen")

    def get_user(self, obj):
        return obj.user.username

    def get_last_seen(self, obj):
        return obj.last_seen.strftime('%Y-%m-%d %H:%M:%S')
