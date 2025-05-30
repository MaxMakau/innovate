from django.shortcuts import render
from services.models import BlogSection, UpcomingEvent,Achievement,Startup
from startups.models import Startup  # Updated import

def homepage(request):
    startups = list(Startup.objects.all().order_by('-registrationDate')[:3])
    achievements = Achievement.objects.all()
    latest_blog = list(BlogSection.objects.all().order_by('-created_date')[:3])
    upcoming_events = list(UpcomingEvent.objects.all().order_by('-created_date')[:3])  # Get 3 upcoming events
    context = {
        'latest_blog': latest_blog,
        'upcoming_events': upcoming_events,
        'startups': startups,
        'achievements' : achievements
    }
    return render(request, 'services/homepage.html', context)



