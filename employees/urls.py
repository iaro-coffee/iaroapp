from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import EmployeeProfileView, LoginView, RegisterView

urlpatterns = [
    path("profile", EmployeeProfileView.as_view(), name="profile"),
    path("register", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
