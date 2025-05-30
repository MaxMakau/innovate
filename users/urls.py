from django.urls import path
from . import views
from users.views import PasswordResetView
from django.urls import include


urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('register/', views.register_view, name='register'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
     path('custom_admin/', include('custom_admin.urls', namespace='custom_admin')),
]