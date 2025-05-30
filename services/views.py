from django.shortcuts import render
from services.models import BlogSection, UpcomingEvent,Achievement
from startups.models import Startup  # Updated import

def homepage(request):
    startups = list(Startup.objects.all()
    achievements = Achievement.objects.all()
    latest_blog = list(BlogSection.objects.all()
    upcoming_events = list(UpcomingEvent.objects.all()
    context = {
        'latest_blog': latest_blog,
        'upcoming_events': upcoming_events,
        'startups': startups,
        'achievements' : achievements
    }
    return render(request, 'services/homepage.html', context)



