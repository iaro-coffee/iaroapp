from django.urls import path, include
from . import views

urlpatterns = [
    path('card/login/', views.UserLoginView.as_view(), name='customer_login'),
    path('card/register/', views.UserSignupView.as_view(), name='customer_register'),
    path('card/', include('allauth.urls')),
]
