from rest_framework.routers import DefaultRouter

from my_app.api.views import ConversationViewSet, MessageViewSet, UserStatusViewSet
from users.api.views import UserViewSet

router = DefaultRouter()

router.register("conversations", ConversationViewSet)
router.register("users", UserViewSet)
router.register("messages", MessageViewSet)
router.register("user_status", UserStatusViewSet)

app_name = "api"
urlpatterns = router.urls
