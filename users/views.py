from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import User
from courses.models import Enrollment, Lesson, LessonProgress
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView, 
    PasswordResetCompleteView
)
from django.contrib.messages.views import SuccessMessageMixin
from users.models import Activity, Notification
from django.db.models import Sum
from courses.models import Course, Enrollment, Lesson, LessonProgress
from .models import Notification


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:

        if request.user.is_superuser:
            return redirect('custom_admin:dashboard')
        
        return redirect_user_dashboard(request.user)
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name}!")
                if user.is_superuser:
                    return redirect('custom_admin:dashboard')
                return redirect_user_dashboard(user)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})

def redirect_user_dashboard(user):
   return redirect('users:dashboard')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('users:login')

@login_required
def dashboard_view(request):
    user = request.user

    # Enrollments
    enrollments = Enrollment.objects.filter(student=user)
    enrolled_courses_count = enrollments.count()

    completed_courses_count = 0
    total_hours = 0

    for enrollment in enrollments:
        course = enrollment.course

        total_lessons = Lesson.objects.filter(module__course=course).count()

        completed_lessons = LessonProgress.objects.filter(
            enrollment=enrollment, is_completed=True
        ).values_list('lesson', flat=True)

        # Sum durations of completed lessons
        lesson_hours = Lesson.objects.filter(id__in=completed_lessons).aggregate(
            total_duration=Sum('duration')
        )['total_duration'] or 0

        total_hours += lesson_hours

        if total_lessons > 0 and len(completed_lessons) == total_lessons:
            completed_courses_count += 1

    all_courses_count = Course.objects.count()

    context = {
        'enrolled_courses': enrolled_courses_count,
        'completed_courses': completed_courses_count,
        'total_hours': round(total_hours, 2),
        'all_courses': all_courses_count,
        'recent_activities': Activity.objects.filter(user=request.user)[:5],
        'notifications_count': Notification.objects.filter(user=request.user, is_read=False).count(),

    }

    return render(request, 'users/dashboard.html', context)



@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    if request.method == 'POST':
        # Handle profile update
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        profile_picture = request.FILES.get('profile_picture')
        
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone_number = phone_number
        
        if profile_picture:
            user.profile_picture = profile_picture
            
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('users:profile')
        
    context = {
        'user': request.user
    }
    return render(request, 'users/profile.html', context)

def register_view(request):
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('users:register')

        # Check if user exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('users:register')

        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number
        )

        login(request, user)
        messages.success(request, f"Welcome to Elevate Academy, {user.first_name}!")
        return redirect('users:dashboard')

    return render(request, 'users/login.html')

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    
    # Optionally mark all as read
    notifications.update(is_read=True)

    context = {
        'notifications': notifications
    }
    return render(request, 'users/notifications.html', context)


class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')
    success_message = "We've emailed you instructions for setting your password. " \
                     "If you don't receive an email, please make sure you've entered " \
                     "the address you registered with."

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')
    success_message = "Your password has been successfully reset. You can now login with your new password."

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'
