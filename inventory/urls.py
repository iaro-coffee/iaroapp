from django.urls import path

from . import views


urlpatterns = [
    path('<str:branch>', views.index, name='inventory'),
    path('evaluation', views.inventory_evaluation, name='inventory_evaluation'),
]