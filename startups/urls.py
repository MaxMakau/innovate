from django.urls import path
from .views import startups, startup_detail

app_name = 'startups'

urlpatterns = [
    path('', startups, name='startups'),  # URL for the list of startups
    path('startup/<int:startup_id>/', startup_detail, name='startup_detail'),  # URL for startup details
]
