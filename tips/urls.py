from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='tips'),
    path('evaluation', views.evaluation, name='evaluation'),
]

# Add URLConf to create, update, and delete tasks
urlpatterns += [
    path('tips/create/', views.TipsCreate.as_view(), name='tips-create'),
]