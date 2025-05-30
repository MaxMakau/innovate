from django.shortcuts import render, get_object_or_404
from services.models import BlogSection, UpcomingEvent,Achievement
from .models import Startup

def startups(request):
    startups = Startup.objects.all()
    latest_blog = BlogSection.objects.all()
    achievements = Achievement.objects.all()
    upcoming_events = UpcomingEvent.objects.all()  
    
    context = {
        'latest_blog': latest_blog,
        'upcoming_events': upcoming_events,
        'startups': startups,
        'achievements': achievements
    }
    return render(request, 'startups/startups.html', context)

def startup_detail(request, startup_id):
    # Retrieve the specific startup by ID
    startup = get_object_or_404(Startup, id=startup_id)
    context = {
        'startup': startup
    }
    return render(request, 'startups/startup_detail.html', context)




