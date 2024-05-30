from django.urls import path, include
from allauth.account import views as allauth_views
from . import views

urlpatterns = [
    path('card/dashboard', views.CustomerIndexView.as_view(), name='customer_index'),

    path('card/login/', views.CustomerLoginView.as_view(), name='customer_login'),
    path('card/register/', views.CustomerSignupView.as_view(), name='customer_register'),
    path('card/logout/', views.CustomLogoutView.as_view(), name='user_logout'),
    path('card/verify-email/<key>/', views.CustomerEmailVerificationView.as_view(), name='verify_email'),

    # Custom Allauh url names for password reset
    path('card/password/reset/', allauth_views.password_reset, name='customer_password_reset'),
    path('card/password/reset/done/', allauth_views.password_reset_done, name='customer_password_reset_done'),
    path('card/password/reset/key/done/', allauth_views.password_reset_from_key_done,
         name='customer_password_reset_from_key_done'),
    path('card/password/reset/key/<uidb36>/<key>/', allauth_views.password_reset_from_key,
         name='customer_password_reset_from_key'),

    path('card/', include('allauth.urls')),
]
