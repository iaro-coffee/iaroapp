from django.urls import path
from .views import Profile, RegisterView

urlpatterns = [
    path("profile", Profile.as_view(), name="profile"),
    path("register", RegisterView.as_view(), name="register"),
]

