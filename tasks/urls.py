from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('overview/', views.TaskListView.as_view(), name='tasks'),
    path('task/<int:pk>', views.TaskDetailView.as_view(), name='task-detail'),
]

# Add URLConf for librarian to renew a task.
urlpatterns += [
    path('task/<uuid:pk>/renew/', views.renew_task_librarian, name='renew-task-librarian'),
]

# Add URLConf to create, update, and delete tasks
urlpatterns += [
    path('task/create/', views.TaskCreate.as_view(), name='task-create'),
    path('task/<int:pk>/update/', views.TaskUpdate.as_view(), name='task-update'),
    path('task/<int:pk>/delete/', views.TaskDelete.as_view(), name='task-delete'),
]
