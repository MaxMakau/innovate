from django.contrib import admin
from .models import Startup

@admin.register(Startup)
class StartupAdmin(admin.ModelAdmin):
    list_display = ('name', 'team_size', 'funding','country', 'registrationDate')
    search_fields = ('name', 'industry')
    list_filter = ('country',)
    ordering = ('name',)
