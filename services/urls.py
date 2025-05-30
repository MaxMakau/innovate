from django.urls import path
from . import views

app_name = 'services'  # This provides URL namespace

urlpatterns = [
    # Homepage
    path('', views.homepage, name='homepage'),
] 