from django.shortcuts import render
from services.models import BlogSection, UpcomingEvent,Achievement
from startups.models import Startup

def homepage(request):
    startups = Startup.objects.all()
    achievements = Achievement.objects.all()
    latest_blog = BlogSection.objects.all()
    upcoming_events = UpcomingEvent.objects.all()  # Get 3 upcoming events
    context = {
        'latest_blog': latest_blog,
        'upcoming_events': upcoming_events,
        'startups': startups,
        'achievements' : achievements
    }
    return render(request, 'services/homepage.html', context)



