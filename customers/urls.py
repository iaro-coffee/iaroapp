from django.urls import path, include
from . import views

urlpatterns = [
    path('accounts/login/', views.UserLoginView.as_view(), name='customer_login'),
    path('accounts/register/', views.UserSignupView.as_view(), name='customer_register'),
    path('accounts/', include('allauth.urls')),
]
