from django.urls import path

from my_app.consumers import ChatConsumer, NotificationConsumer, UserStatusConsumer

websocket_urlpatterns = [
    path('chats/<conversation_name>/', ChatConsumer.as_asgi()),
    path("notifications/", NotificationConsumer.as_asgi()),
    path("status/", UserStatusConsumer.as_asgi()),
]
