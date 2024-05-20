from django.contrib.auth.views import (
    LogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)
from django.urls import path, reverse_lazy
from .views import Profile, RegisterView, LoginView

urlpatterns = [
    path("profile", Profile.as_view(), name="profile"),
    path("register", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]