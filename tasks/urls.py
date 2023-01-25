from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('overview/', views.TaskListView.as_view(), name='tasks'),
    path('task/<int:pk>', views.TaskDetailView.as_view(), name='task-detail'),
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('author/<int:pk>',
         views.AuthorDetailView.as_view(), name='author-detail'),
]


urlpatterns += [
    path('mytasks/', views.LoanedTasksByUserListView.as_view(), name='my-borrowed'),
    path(r'borrowed/', views.LoanedTasksAllListView.as_view(), name='all-borrowed'),  # Added for challenge
]


# Add URLConf for librarian to renew a task.
urlpatterns += [
    path('task/<uuid:pk>/renew/', views.renew_task_librarian, name='renew-task-librarian'),
]


# Add URLConf to create, update, and delete authors
urlpatterns += [
    path('author/create/', views.AuthorCreate.as_view(), name='author-create'),
    path('author/<int:pk>/update/', views.AuthorUpdate.as_view(), name='author-update'),
    path('author/<int:pk>/delete/', views.AuthorDelete.as_view(), name='author-delete'),
]

# Add URLConf to create, update, and delete tasks
urlpatterns += [
    path('task/create/', views.TaskCreate.as_view(), name='task-create'),
    path('task/<int:pk>/update/', views.TaskUpdate.as_view(), name='task-update'),
    path('task/<int:pk>/delete/', views.TaskDelete.as_view(), name='task-delete'),
]
