# courses/urls.py
from django.urls import path
from . import views

app_name = 'courses'  # This provides URL namespace

urlpatterns = [
    # Course listing (changed from 'courselist/' to just '/')
    path('', views.CourseListView.as_view(), name='course_list'),
    path('personalized/', views.personalized_courses_view, name='personalized'),
    

    # Course details, checkout, payment, modules, and progress now use SLUG
    # Changed from <int:course_id>/ to <slug:slug>/
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('<slug:slug>/enroll/', views.enroll_course, name='enroll_course'), # New enroll path
    path('<slug:slug>/checkout/', views.course_checkout, name='course_checkout'),
    path('<slug:slug>/process-payment/', views.process_payment, name='process_payment'),
    path('<slug:slug>/modules/', views.module_list, name='module_list'),
    path('<slug:slug>/progress/', views.course_progress, name='course_progress'),
    

    # Lesson paths now use PK (primary key)
    # Changed from <int:lesson_id>/ to <int:pk>/
    path('lesson/<int:pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('lesson/<int:pk>/mark_complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    path('lesson/<int:pk>/update_video_progress/', views.update_video_progress, name='update_video_progress'), # New API endpoint for video progress

    # Quiz paths now use PK (primary key) for quiz_id
    # Changed from <int:lesson_id>/quiz/ to quiz/<int:pk>/ for quiz_detail
    path('quiz/<int:pk>/', views.QuizDetailView.as_view(), name='quiz_detail'),
    path('quiz/<int:pk>/submit/', views.submit_quiz, name='submit_quiz'),
]