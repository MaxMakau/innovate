from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard_view, name='dashboard'),

    # Course Management
    path('courses/', views.course_list_view, name='course_list'),
    path('courses/create/', views.course_create_view, name='course_create'),
    path('courses/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('courses/<int:course_id>/update/', views.course_update_view, name='course_update'),
    path('courses/<int:course_id>/delete/', views.course_delete_view, name='course_delete'),

    # Module Management
    path('courses/<int:course_id>/modules/create/', views.module_create_view, name='module_create'),
    path('modules/<int:module_id>/update/', views.module_update_view, name='module_update'),
    path('modules/<int:module_id>/delete/', views.module_delete_view, name='module_delete'),

    # Lesson Management
    path('modules/<int:module_id>/lessons/create/', views.lesson_create_view, name='lesson_create'),
    path('lessons/<int:lesson_id>/update/', views.lesson_update_view, name='lesson_update'),
    path('lessons/<int:lesson_id>/delete/', views.lesson_delete_view, name='lesson_delete'),

    # Quiz Management
    path('lessons/<int:lesson_id>/quiz/create/', views.quiz_create_view, name='quiz_create'),
    path('quizzes/<int:quiz_id>/update/', views.quiz_update_view, name='quiz_update'),
    path('quizzes/<int:quiz_id>/delete/', views.quiz_delete_view, name='quiz_delete'),
    path('quizzes/<int:quiz_id>/', views.quiz_detail_view, name='quiz_detail'),

    # Question Management
    path('quizzes/<int:quiz_id>/questions/create/', views.question_create_view, name='question_create'),
    path('questions/<int:question_id>/update/', views.question_update_view, name='question_update'),
    path('questions/<int:question_id>/delete/', views.question_delete_view, name='question_delete'),

    # User Progress
    path('user-progress/', views.user_progress_view, name='user_progress'),
    path('enrollment/<int:enrollment_id>/progress/', views.enrollment_progress_view, name='enrollment_progress'),
    path('enrollment/<int:enrollment_id>/reset/', views.reset_progress_view, name='reset_progress'),
    path('user-progress/export/', views.export_progress_view, name='export_progress'),

    # Blog & Events
    path('blog-event/create/', views.add_blog_event_view, name='add_blog_event'),
    path('blog-event/<int:pk>/update/', views.update_blog_event_view, name='update_blog_event'),
    path('blog-event/<int:pk>/delete/', views.delete_blog_event_view, name='delete_blog_event'),
    path('blog-event/list/', views.blog_event_list_view, name='blog_event_list'),

    # Startup Management
    path('startup/list/', views.startup_list_view, name='startup_list'),
    path('startup/create/', views.add_startup_view, name='add_startup'),
    path('startup/<int:startup_id>/update/', views.update_startup_view, name='update_startup'),
    path('startup/<int:startup_id>/delete/', views.delete_startup_view, name='delete_startup'),
]