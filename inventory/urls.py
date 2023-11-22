from django.urls import path

from . import views


urlpatterns = [
    path('evaluation', views.inventory_evaluation, name='inventory_evaluation'),
    path('<str:branch>', views.index, name='inventory'),
]