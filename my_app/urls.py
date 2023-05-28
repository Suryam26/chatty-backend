from django.urls import path

from .views import CustomObtainAuthTokenView

urlpatterns = [
    path('auth-token/', CustomObtainAuthTokenView.as_view()),
]