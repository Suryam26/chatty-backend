import uuid

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    online = models.ManyToManyField(to=User, blank=True)

    def get_online_count(self):
        return self.online.count()

    def join(self, user):
        self.online.add(user)
        self.save()

    def leave(self, user):
        self.online.remove(user)
        self.save()

    def __str__(self):
        return f"{self.name} ({self.get_online_count()})"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_from_me"
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="messages_to_me"
    )
    content = models.CharField(max_length=512)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def delete(self):
        self.is_deleted = True
        self.content = "This message has been deleted"
        self.save()

    def __str__(self):
        return f"From {self.from_user.username} to {self.to_user.username}: {self.content} [{self.timestamp}]"


class UserStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="status")
    last_seen = models.DateTimeField(default=timezone.now)
    online = models.BooleanField(default=False)

    def join(self):
        self.online = True
        self.save()

    def leave(self):
        self.online = False
        self.last_seen = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user} ({'online' if self.online else f'last seen:{self.last_seen}'})"
