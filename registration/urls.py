from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='registration'),
    path('register', views.index, name="register")
]