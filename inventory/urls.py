from django.urls import path

from . import views


urlpatterns = [
    path('evaluation', views.inventory_evaluation, name='inventory_evaluation'),
    path('shopping', views.inventory_shopping, name='inventory_shopping'),
    path('populate', views.inventory_populate, name='inventory_populate'),
    path('packaging', views.inventory_packaging, name='inventory_packaging'),
]