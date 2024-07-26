"""iaroapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

# Use include() to add URLS from the tasks application and authentication system
from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin/", admin.site.urls),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("inventory/", include("inventory.urls")),
    path("procedures/", include("procedures.urls")),
    path("shifts/", include("shifts.urls")),
    path("ratings/", include("ratings.urls")),
    path("tasks/", include("tasks.urls")),
    path("users/", include("users.urls")),
    path("notes/", include("interactions.urls")),  # Updated path
    path("", include("customers.urls")),
    path(
        "get_populartimes_data/",
        views.get_populartimes_data,
        name="get_populartimes_data",
    ),
]

# Use static() to add url mapping to serve static files during development (only)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
