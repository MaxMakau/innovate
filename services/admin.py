from django.contrib import admin
from .models import BlogSection, UpcomingEvent, Achievement

@admin.register(BlogSection)
class BlogSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_date', 'updated_date')
    search_fields = ('title', 'author', 'content')
    list_filter = ('created_date', 'author')

@admin.register(UpcomingEvent)
class UpcomingEventAdmin(admin.ModelAdmin):
    list_display = ('description', 'created_date')
    search_fields = ('description',)
    list_filter = ('created_date',)

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'image', 'created_date')
    search_fields = ('title',)
    list_filter = ('created_date',)
 