from django.shortcuts import render, redirect,  get_object_or_404, Http404
from courses.models import Course, Module, Lesson, Quiz, Enrollment, Question, Option, VideoLesson, TextLesson
from .forms import CourseForm, ModuleForm, LessonForm,VideoLessonForm, TextLessonForm, QuestionForm, OptionForm, QuizForm, BlogEventForm  # Create these forms in forms.py
from users.models import User
from services.models import BlogSection, UpcomingEvent
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from startups.models import Startup
from .forms import StartupForm
from django.db import transaction
from django.db.models import Q
from django.forms import inlineformset_factory
import logging

# Configure logging
logger = logging.getLogger(__name__)

# View to add a course along with its modules and lessons
@login_required
def course_list_view(request):
    """
    Displays a list of all courses with filtering and sorting options.
    """
    courses = Course.objects.select_related('category', 'instructor').all()
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        courses = courses.filter(status=status)
    
    # Filter by level if provided
    level = request.GET.get('level')
    if level:
        courses = courses.filter(level=level)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Sort by different fields
    sort_by = request.GET.get('sort', '-created_date')
    if sort_by == 'title':
        courses = courses.order_by('title')
    elif sort_by == 'price':
        courses = courses.order_by('price')
    elif sort_by == 'duration':
        courses = courses.order_by('duration')
    else:
        courses = courses.order_by('-created_date')
    
    context = {
        'courses': courses,
        'status_choices': Course.STATUS_CHOICES,
        'level_choices': Course._meta.get_field('level').choices,
        'current_status': status,
        'current_level': level,
        'current_sort': sort_by,
        'search_query': search_query,
    }
    return render(request, 'custom_admin/course_list.html', context)


@login_required
def course_create_view(request):
    """
    Allows an administrator to create a new Course.
    """
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.title}" created successfully!')
            return redirect('custom_admin:course_detail', course_id=course.pk)
        else:
            messages.error(request, 'Error creating course. Please check the form.')
    else:
        form = CourseForm()
    
    context = {'form': form, 'title': 'Create New Course'}
    return render(request, 'custom_admin/course_form.html', context)


@login_required
def course_detail_view(request, course_id):
    """
    Displays details of a specific course, its modules, and lessons.
    Also provides links/forms to add related content.
    """
    course = get_object_or_404(Course, pk=course_id)
    modules = course.modules.all() # Fetch modules related to this course

    context = {
        'course': course,
        'modules': modules,
    }
    return render(request, 'custom_admin/course_detail.html', context)


@login_required
def course_update_view(request, course_id):
    """
    Allows updating an existing Course.
    """
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course "{course.title}" updated successfully!')
            return redirect('custom_admin:course_detail', course_id=course.pk)
        else:
            messages.error(request, 'Error updating course. Please check the form.')
    else:
        form = CourseForm(instance=course)
    
    context = {'form': form, 'course': course, 'title': f'Update Course: {course.title}'}
    return render(request, 'custom_admin/course_form.html', context)


@login_required
def course_delete_view(request, course_id):
    """
    Deletes a specific Course.
    """
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        course.delete()
        messages.success(request, f'Course "{course.title}" deleted successfully.')
        return redirect('custom_admin:course_list')
    
    context = {'course': course}
    return render(request, 'custom_admin/course_confirm_delete.html', context)


# --- Module Management Views ---

@login_required
def module_create_view(request, course_id):
    """
    Allows creating a new Module with multiple lessons for a specific Course.
    """
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        # Initialize form with course instance
        form = ModuleForm(request.POST, initial={'course': course})
        logger.info(f"Processing module creation for course {course_id}")
        logger.debug(f"POST data: {request.POST}")
        logger.debug(f"FILES data: {request.FILES}")
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the module with automatic order
                    module = form.save(commit=False)
                    module.course = course
                    module.order = Module.get_next_order(course)
                    module.save()
                    logger.info(f"Module created successfully: {module.title}")

                    # Get all lesson data from the form
                    lesson_titles = request.POST.getlist('lesson_title[]')
                    lesson_descriptions = request.POST.getlist('lesson_description[]')
                    lesson_types = request.POST.getlist('lesson_type[]')
                    
                    logger.debug(f"Lesson data received - Titles: {lesson_titles}, Types: {lesson_types}")

                    # Create lessons with automatic order
                    for i in range(len(lesson_titles)):
                        if lesson_titles[i]:  # Only create if title is provided
                            try:
                                lesson = Lesson.objects.create(
                                    module=module,
                                    title=lesson_titles[i],
                                    description=lesson_descriptions[i],
                                    lesson_type=lesson_types[i],
                                    order=Lesson.get_next_order(module)
                                )
                                logger.info(f"Lesson created: {lesson.title} (Type: {lesson.lesson_type})")

                                # Handle lesson-specific content
                                if lesson_types[i] == 'video':
                                    video_file = request.FILES.getlist('video_file[]')[i] if i < len(request.FILES.getlist('video_file[]')) else None
                                    video_url = request.POST.getlist('video_url[]')[i] if i < len(request.POST.getlist('video_url[]')) else None
                                    
                                    logger.debug(f"Video lesson data - File: {video_file}, URL: {video_url}")
                                    
                                    VideoLesson.objects.create(
                                        lesson=lesson,
                                        video_file=video_file,
                                        video_url=video_url
                                    )
                                    logger.info(f"Video lesson content created for lesson: {lesson.title}")
                                    
                                elif lesson_types[i] == 'text':
                                    text_content = request.POST.getlist('text_content[]')[i] if i < len(request.POST.getlist('text_content[]')) else None
                                    document_file = request.FILES.getlist('document_file[]')[i] if i < len(request.FILES.getlist('document_file[]')) else None
                                    
                                    logger.debug(f"Text lesson data - Content length: {len(text_content) if text_content else 0}, Document: {document_file}")
                                    
                                    TextLesson.objects.create(
                                        lesson=lesson,
                                        content=text_content,
                                        document_file=document_file
                                    )
                                    logger.info(f"Text lesson content created for lesson: {lesson.title}")
                            except Exception as e:
                                logger.error(f"Error creating lesson {i+1}: {str(e)}")
                                raise

                    messages.success(request, f'Module "{module.title}" with {len(lesson_titles)} lessons added successfully.')
                    return redirect('custom_admin:course_detail', course_id=course.pk)
            except Exception as e:
                logger.error(f"Transaction failed: {str(e)}")
                messages.error(request, f'Error creating module and lessons: {str(e)}')
        else:
            logger.error(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                logger.error(f"Field '{field}' errors: {errors}")
            messages.error(request, 'Error adding module. Please check the form.')
    else:
        # Initialize form with course instance for GET request
        form = ModuleForm(initial={'course': course})
    
    context = {'form': form, 'course': course, 'title': f'Add Module to {course.title}'}
    return render(request, 'custom_admin/module_form.html', context)


@login_required
def module_update_view(request, module_id):
    """
    Allows updating an existing Module and its lessons.
    """
    module = get_object_or_404(Module, pk=module_id)
    course = module.course
    
    if request.method == 'POST':
        form = ModuleForm(request.POST, instance=module)
        logger.info(f"Processing module update for module {module_id}")
        logger.debug(f"POST data: {request.POST}")
        logger.debug(f"FILES data: {request.FILES}")
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update the module
                    module = form.save()
                    logger.info(f"Module updated successfully: {module.title}")

                    # Get all lesson data from the form
                    lesson_titles = request.POST.getlist('lesson_title[]')
                    lesson_descriptions = request.POST.getlist('lesson_description[]')
                    lesson_types = request.POST.getlist('lesson_type[]')
                    
                    logger.debug(f"Lesson data received - Titles: {lesson_titles}, Types: {lesson_types}")

                    # Update existing lessons and create new ones
                    existing_lessons = list(module.lessons.all())
                    for i in range(len(lesson_titles)):
                        if lesson_titles[i]:  # Only process if title is provided
                            try:
                                if i < len(existing_lessons):
                                    # Update existing lesson
                                    lesson = existing_lessons[i]
                                    lesson.title = lesson_titles[i]
                                    lesson.description = lesson_descriptions[i]
                                    lesson.lesson_type = lesson_types[i]
                                    lesson.save()
                                    logger.info(f"Lesson updated: {lesson.title} (Type: {lesson.lesson_type})")
                                else:
                                    # Create new lesson
                                    lesson = Lesson.objects.create(
                                        module=module,
                                        title=lesson_titles[i],
                                        description=lesson_descriptions[i],
                                        lesson_type=lesson_types[i],
                                        order=Lesson.get_next_order(module)
                                    )
                                    logger.info(f"New lesson created: {lesson.title} (Type: {lesson.lesson_type})")

                                # Handle lesson-specific content
                                if lesson_types[i] == 'video':
                                    video_file = request.FILES.getlist('video_file[]')[i] if i < len(request.FILES.getlist('video_file[]')) else None
                                    video_url = request.POST.getlist('video_url[]')[i] if i < len(request.POST.getlist('video_url[]')) else None
                                    
                                    logger.debug(f"Video lesson data - File: {video_file}, URL: {video_url}")
                                    
                                    # Update or create video lesson
                                    video_lesson, created = VideoLesson.objects.get_or_create(lesson=lesson)
                                    if video_file:
                                        video_lesson.video_file = video_file
                                    if video_url:
                                        video_lesson.video_url = video_url
                                    video_lesson.save()
                                    logger.info(f"Video lesson content {'created' if created else 'updated'} for lesson: {lesson.title}")
                                    
                                elif lesson_types[i] == 'text':
                                    text_content = request.POST.getlist('text_content[]')[i] if i < len(request.POST.getlist('text_content[]')) else None
                                    document_file = request.FILES.getlist('document_file[]')[i] if i < len(request.FILES.getlist('document_file[]')) else None
                                    
                                    logger.debug(f"Text lesson data - Content length: {len(text_content) if text_content else 0}, Document: {document_file}")
                                    
                                    # Update or create text lesson
                                    text_lesson, created = TextLesson.objects.get_or_create(lesson=lesson)
                                    if text_content:
                                        text_lesson.content = text_content
                                    if document_file:
                                        text_lesson.document_file = document_file
                                    text_lesson.save()
                                    logger.info(f"Text lesson content {'created' if created else 'updated'} for lesson: {lesson.title}")
                            except Exception as e:
                                logger.error(f"Error processing lesson {i+1}: {str(e)}")
                                raise

                    # Delete any remaining lessons that weren't updated
                    for lesson in existing_lessons[len(lesson_titles):]:
                        lesson.delete()
                        logger.info(f"Deleted lesson: {lesson.title}")

                    messages.success(request, f'Module "{module.title}" with {len(lesson_titles)} lessons updated successfully.')
                    return redirect('custom_admin:course_detail', course_id=course.pk)
            except Exception as e:
                logger.error(f"Transaction failed: {str(e)}")
                messages.error(request, f'Error updating module and lessons: {str(e)}')
        else:
            logger.error(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                logger.error(f"Field '{field}' errors: {errors}")
            messages.error(request, 'Error updating module. Please check the form.')
    else:
        form = ModuleForm(instance=module)
    
    context = {
        'form': form,
        'module': module,
        'course': course,
        'title': f'Update Module: {module.title}'
    }
    return render(request, 'custom_admin/module_form.html', context)


@login_required
def module_delete_view(request, module_id):
    """
    Deletes a specific Module.
    """
    module = get_object_or_404(Module, pk=module_id)
    course_id = module.course.pk # Store course ID before deletion
    if request.method == 'POST':
        module.delete()
        messages.success(request, f'Module "{module.title}" deleted successfully.')
        return redirect('custom_admin:course_detail', course_id=course_id)
    
    context = {'module': module}
    return render(request, 'custom_admin/module_confirm_delete.html', context)


# --- Lesson Management Views ---

@login_required
def lesson_create_view(request, module_pk):
    """
    Allows creating a new Lesson for a specific Module.
    Handles different lesson types (Video, Text).
    """
    module = get_object_or_404(Module, pk=module_pk)
    
    if request.method == 'POST':
        lesson_form = LessonForm(request.POST)
        video_form = VideoLessonForm(request.POST, request.FILES)
        text_form = TextLessonForm(request.POST, request.FILES)

        if lesson_form.is_valid():
            lesson = lesson_form.save(commit=False)
            lesson.module = module
            lesson.order = Lesson.get_next_order(module)
            
            lesson_type = lesson_form.cleaned_data['lesson_type']
            
            with transaction.atomic(): # Ensure all saves happen or none do
                lesson.save()
                if lesson_type == 'video':
                    if video_form.is_valid():
                        video_lesson = video_form.save(commit=False)
                        video_lesson.lesson = lesson
                        video_lesson.save()
                        messages.success(request, f'Video Lesson "{lesson.title}" added successfully.')
                        return redirect('custom_admin:course_detail', pk=module.course.pk)
                    else:
                        messages.error(request, 'Error adding video lesson content. Please check the video form.')
                elif lesson_type == 'text':
                    if text_form.is_valid():
                        text_lesson = text_form.save(commit=False)
                        text_lesson.lesson = lesson
                        text_lesson.save()
                        messages.success(request, f'Text Lesson "{lesson.title}" added successfully.')
                        return redirect('custom_admin:course_detail', pk=module.course.pk)
                    else:
                        messages.error(request, 'Error adding text lesson content. Please check the text form.')
                else:
                    messages.error(request, 'Invalid lesson type selected.')
        else:
            messages.error(request, 'Error creating lesson. Please check the lesson form.')
    else:
        lesson_form = LessonForm()
        video_form = VideoLessonForm()
        text_form = TextLessonForm()

    context = {
        'lesson_form': lesson_form,
        'video_form': video_form,
        'text_form': text_form,
        'module': module,
        'title': f'Add Lesson to {module.title}'
    }
    return render(request, 'custom_admin/lesson_form.html', context)


@login_required
def lesson_update_view(request, lesson_pk):
    """
    Allows updating an existing Lesson and its associated content (VideoLesson/TextLesson).
    """
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    video_lesson = None
    text_lesson = None

    if lesson.lesson_type == 'video':
        video_lesson = getattr(lesson, 'videolesson', None)
    elif lesson.lesson_type == 'text':
        text_lesson = getattr(lesson, 'textlesson', None)

    if request.method == 'POST':
        lesson_form = LessonForm(request.POST, instance=lesson)
        video_form = VideoLessonForm(request.POST, request.FILES, instance=video_lesson) if video_lesson else VideoLessonForm(request.POST, request.FILES)
        text_form = TextLessonForm(request.POST, request.FILES, instance=text_lesson) if text_lesson else TextLessonForm(request.POST, request.FILES)

        if lesson_form.is_valid():
            with transaction.atomic():
                lesson_form.save()
                
                lesson_type = lesson_form.cleaned_data['lesson_type']

                if lesson_type == 'video':
                    if video_form.is_valid():
                        vl_instance = video_form.save(commit=False)
                        vl_instance.lesson = lesson
                        vl_instance.save()
                        messages.success(request, f'Video Lesson "{lesson.title}" updated successfully.')
                        return redirect('custom_admin:course_detail', pk=lesson.module.course.pk)
                    else:
                        messages.error(request, 'Error updating video lesson content. Please check the video form.')
                elif lesson_type == 'text':
                    if text_form.is_valid():
                        tl_instance = text_form.save(commit=False)
                        tl_instance.lesson = lesson
                        tl_instance.save()
                        messages.success(request, f'Text Lesson "{lesson.title}" updated successfully.')
                        return redirect('custom_admin:course_detail', pk=lesson.module.course.pk)
                    else:
                        messages.error(request, 'Error updating text lesson content. Please check the text form.')
                else:
                    messages.error(request, 'Invalid lesson type selected.')
        else:
            messages.error(request, 'Error updating lesson. Please check the lesson form.')
    else:
        lesson_form = LessonForm(instance=lesson)
        video_form = VideoLessonForm(instance=video_lesson)
        text_form = TextLessonForm(instance=text_lesson)

    context = {
        'lesson_form': lesson_form,
        'video_form': video_form,
        'text_form': text_form,
        'lesson': lesson,
        'title': f'Update Lesson: {lesson.title}'
    }
    return render(request, 'custom_admin/lesson_form.html', context)


@login_required
def lesson_delete_view(request, lesson_pk):
    """
    Deletes a specific Lesson.
    """
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    course_pk = lesson.module.course.pk # Store course PK before deletion
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, f'Lesson "{lesson.title}" deleted successfully.')
        return redirect('custom_admin:course_detail', pk=course_pk)
    
    context = {'lesson': lesson}
    return render(request, 'custom_admin/lesson_confirm_delete.html', context)


# --- Quiz Management Views (Simplified) ---

@login_required
@login_required
def quiz_create_view(request, lesson_pk):
    """
    Allows creating a new Quiz for a specific Lesson.
    """
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.lesson = lesson
            quiz.save()
            messages.success(request, f'Quiz "{quiz.title}" added to "{lesson.title}".')
            return redirect('custom_admin:quiz_detail', pk=quiz.pk)
        else:
            messages.error(request, 'Error adding quiz. Please check the form.')
    else:
        form = QuizForm()
    
    context = {'form': form, 'lesson': lesson, 'title': f'Add Quiz to {lesson.title}'}
    return render(request, 'custom_admin/quiz_form.html', context)


@login_required
def quiz_update_view(request, pk):
    """
    Allows updating an existing Quiz.
    """
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, f'Quiz "{quiz.title}" updated successfully.')
            return redirect('custom_admin:quiz_detail', pk=quiz.pk)
        else:
            messages.error(request, 'Error updating quiz. Please check the form.')
    else:
        form = QuizForm(instance=quiz)
    
    context = {
        'form': form,
        'quiz': quiz,
        'title': f'Update Quiz: {quiz.title}'
    }
    return render(request, 'custom_admin/quiz_form.html', context)


@login_required
def quiz_delete_view(request, pk):
    """
    Deletes a specific Quiz.
    """
    quiz = get_object_or_404(Quiz, pk=pk)
    lesson_pk = quiz.lesson.pk  # Store lesson PK before deletion
    
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, f'Quiz "{quiz.title}" deleted successfully.')
        return redirect('custom_admin:lesson_detail', pk=lesson_pk)
    
    context = {'quiz': quiz}
    return render(request, 'custom_admin/quiz_confirm_delete.html', context)


@login_required
def quiz_detail_view(request, pk):
    """
    Displays details of a specific quiz and allows adding/managing questions.
    """
    quiz = get_object_or_404(Quiz, pk=pk)
    questions = quiz.questions.all().order_by('order')

    context = {
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'custom_admin/quiz_detail.html', context)


@login_required
def question_create_view(request, quiz_pk):
    """
    Allows creating a new Question for a specific Quiz.
    """
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    OptionFormSet = inlineformset_factory(Question, Option, form=OptionForm, extra=4, can_delete=False)

    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.quiz = quiz
            
            with transaction.atomic():
                question.save()
                option_formset = OptionFormSet(request.POST, instance=question)
                if option_formset.is_valid():
                    option_formset.save()
                    messages.success(request, 'Question and options added successfully!')
                    return redirect('custom_admin:quiz_detail', pk=quiz.pk)
                else:
                    messages.error(request, 'Error adding options. Ensure at least one option is correct.')
                    question.delete() 
        else:
            messages.error(request, 'Error adding question. Please check the question form.')
    else:
        question_form = QuestionForm()
        option_formset = OptionFormSet(instance=None)

    context = {
        'question_form': question_form,
        'option_formset': option_formset,
        'quiz': quiz,
        'title': f'Add Question to {quiz.title}'
    }
    return render(request, 'custom_admin/question_form.html', context)

@login_required
def question_update_view(request, pk):
    """
    Allows updating an existing Question and its Options.
    """
    question = get_object_or_404(Question, pk=pk)
    quiz = question.quiz
    OptionFormSet = inlineformset_factory(Question, Option, form=OptionForm, extra=1, can_delete=True)

    if request.method == 'POST':
        question_form = QuestionForm(request.POST, instance=question)
        if question_form.is_valid():
            with transaction.atomic():
                question = question_form.save()
                option_formset = OptionFormSet(request.POST, instance=question)
                if option_formset.is_valid():
                    option_formset.save()
                    messages.success(request, 'Question and options updated successfully!')
                    return redirect('custom_admin:quiz_detail', pk=quiz.pk)
                else:
                    messages.error(request, 'Error updating options. Please check the form.')
        else:
            messages.error(request, 'Error updating question. Please check the form.')
    else:
        question_form = QuestionForm(instance=question)
        option_formset = OptionFormSet(instance=question)

    context = {
        'question_form': question_form,
        'option_formset': option_formset,
        'quiz': quiz,
        'title': f'Update Question: {question.title}'
    }
    return render(request, 'custom_admin/question_form.html', context)

@login_required
def question_delete_view(request, pk):
    """
    Deletes a specific Question.
    """
    question = get_object_or_404(Question, pk=pk)
    quiz_pk = question.quiz.pk  # Store quiz PK before deletion
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully.')
        return redirect('custom_admin:quiz_detail', pk=quiz_pk)
    
    context = {'question': question}
    return render(request, 'custom_admin/question_confirm_delete.html', context)
# --- Dashboard and Other Views (Adjusted) ---

@login_required
def admin_dashboard_view(request):
    """
    Admin dashboard showing overall statistics.
    """
    total_courses = Course.objects.count()
    total_users = User.objects.count() # Make sure User is imported
    total_enrollments = Enrollment.objects.count()
    
    # Calculate enrollment progress
    # Note: Using 'is_completed' as per your model
    completed_enrollments = Enrollment.objects.filter(is_completed=True).count()
    progress_percentage = (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0

    # Fetch recent enrollments
    # Renamed 'user' to 'student' in Enrollment model
    recent_enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrollment_date')[:10]

    context = {
        'total_courses': total_courses,
        'total_users': total_users,
        'total_enrollments': total_enrollments,
        'progress_percentage': round(progress_percentage, 2), # Round for display
        'recent_enrollments': recent_enrollments,
    }

    return render(request, 'custom_admin/dashboard.html', context)


@login_required
def user_progress_view(request):
    """
    View to see enrolled users and their progress with filtering and sorting options.
    """
    enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrollment_date')
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        enrollments = enrollments.filter(status=status)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        enrollments = enrollments.filter(
            Q(student__username__icontains=search_query) |
            Q(course__title__icontains=search_query)
        )
    
    # Sort functionality
    sort_by = request.GET.get('sort', 'enrollment_date')
    order = request.GET.get('order', 'desc')
    
    if sort_by == 'progress':
        enrollments = enrollments.order_by(f'{"-" if order == "desc" else ""}progress')
    elif sort_by == 'last_activity':
        enrollments = enrollments.order_by(f'{"-" if order == "desc" else ""}last_activity')
    else:  # enrollment_date
        enrollments = enrollments.order_by(f'{"-" if order == "desc" else ""}enrollment_date')
    
    context = {
        'enrollments': enrollments,
        'current_status': status,
        'current_sort': sort_by,
        'current_order': order,
        'search_query': search_query,
    }
    return render(request, 'custom_admin/user_progress.html', context)

@login_required
def enrollment_progress_view(request, enrollment_id):
    """
    Detailed view of a specific enrollment's progress.
    """
    enrollment = get_object_or_404(Enrollment.objects.select_related('student', 'course'), id=enrollment_id)
    
    # Get all lessons and quizzes for the course
    lessons = enrollment.course.get_all_lessons()
    quizzes = Quiz.objects.filter(lesson__in=lessons)
    
    # Get completion status for each lesson and quiz
    lesson_progress = enrollment.get_lesson_progress()
    quiz_progress = enrollment.get_quiz_progress()
    
    context = {
        'enrollment': enrollment,
        'lessons': lessons,
        'quizzes': quizzes,
        'lesson_progress': lesson_progress,
        'quiz_progress': quiz_progress,
    }
    return render(request, 'custom_admin/enrollment_progress.html', context)

@login_required
def reset_progress_view(request, enrollment_id):
    """
    Reset progress for a specific enrollment.
    """
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    if request.method == 'POST':
        enrollment.reset_progress()
        messages.success(request, 'Progress has been reset successfully.')
        return redirect('custom_admin:enrollment_progress', enrollment_id=enrollment_id)
    
    context = {
        'enrollment': enrollment,
    }
    return render(request, 'custom_admin/reset_progress_confirm.html', context)

@login_required
def export_progress_view(request):
    """
    Export user progress data to CSV.
    """
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    # Get filtered enrollments (reuse filtering logic from user_progress_view)
    enrollments = Enrollment.objects.select_related('student', 'course')
    
    # Apply filters
    status = request.GET.get('status')
    if status:
        enrollments = enrollments.filter(status=status)
    
    search_query = request.GET.get('search')
    if search_query:
        enrollments = enrollments.filter(
            Q(student__username__icontains=search_query) |
            Q(course__title__icontains=search_query)
        )
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="user_progress_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student', 'Course', 'Enrollment Date', 'Progress', 'Status', 'Last Activity'])
    
    for enrollment in enrollments:
        writer.writerow([
            enrollment.student.username,
            enrollment.course.title,
            enrollment.enrollment_date.strftime('%Y-%m-%d'),
            f"{enrollment.progress}%",
            enrollment.status,
            enrollment.last_activity.strftime('%Y-%m-%d %H:%M:%S') if enrollment.last_activity else 'N/A'
        ])
    
    return response

@login_required
def add_blog_event_view(request):
    if request.method == 'POST':
        form = BlogEventForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['type'] == 'blog':
                BlogSection.objects.create(
                    title=form.cleaned_data['title'],
                    content=form.cleaned_data['content'],
                    author=form.cleaned_data['author']
                )
            elif form.cleaned_data['type'] == 'event':
                UpcomingEvent.objects.create(
                    description=form.cleaned_data['description'],
                    image=form.cleaned_data['image']
                )
            return redirect('custom_admin:dashboard')

    else:
        form = BlogEventForm()

    return render(request, 'custom_admin/add_blog_event.html', {'form': form})

@login_required
def update_blog_event_view(request, pk):
    if request.method == 'POST':
        form = BlogEventForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['type'] == 'blog':
                blog = BlogSection.objects.get(pk=pk)
                blog.title = form.cleaned_data['title']
                blog.content = form.cleaned_data['content']
                blog.author = form.cleaned_data['author']
                blog.save()
            elif form.cleaned_data['type'] == 'event':
                event = UpcomingEvent.objects.get(pk=pk)
                event.description = form.cleaned_data['description']
                if form.cleaned_data['image']:
                    event.image = form.cleaned_data['image']
                event.save()
            messages.success(request, 'Content updated successfully.')
            return redirect('custom_admin:blog_event_list')
    else:
        try:
            blog = BlogSection.objects.get(pk=pk)
            form = BlogEventForm(initial={
                'type': 'blog',
                'title': blog.title,
                'content': blog.content,
                'author': blog.author
            })
        except BlogSection.DoesNotExist:
            try:
                event = UpcomingEvent.objects.get(pk=pk)
                form = BlogEventForm(initial={
                    'type': 'event',
                    'description': event.description
                })
            except UpcomingEvent.DoesNotExist:
                raise Http404("Blog or Event not found")

    return render(request, 'custom_admin/add_blog_event.html', {'form': form})

@login_required
def delete_blog_event_view(request, pk):
    if request.method == 'POST':
        try:
            blog = BlogSection.objects.get(pk=pk)
            blog.delete()
        except BlogSection.DoesNotExist:
            try:
                event = UpcomingEvent.objects.get(pk=pk)
                event.delete()
            except UpcomingEvent.DoesNotExist:
                raise Http404("Blog or Event not found")
        return redirect('custom_admin:dashboard')
    
    return render(request, 'custom_admin/delete_blog_event_confirm.html')

@login_required
def add_startup_view(request):
    if request.method == 'POST':
        form = StartupForm(request.POST, request.FILES)
        if form.is_valid():
            startup = form.save()
            messages.success(request, f'Startup "{startup.name}" added successfully.')
            return redirect('custom_admin:dashboard')
        else:
            messages.error(request, 'Error adding startup. Please check the form.')
    else:
        form = StartupForm()
    return render(request, 'custom_admin/add_startup.html', {'form': form})

@login_required
def update_startup_view(request, startup_id):
    startup = get_object_or_404(Startup, pk=startup_id)
    if request.method == 'POST':
        form = StartupForm(request.POST, request.FILES, instance=startup)
        if form.is_valid():
            form.save()
            messages.success(request, f'Startup "{startup.name}" updated successfully.')
            return redirect('custom_admin:dashboard')
        else:
            messages.error(request, 'Error updating startup. Please check the form.')
    else:
        form = StartupForm(instance=startup)
    return render(request, 'custom_admin/update_startup.html', {'form': form, 'startup': startup})

@login_required
def delete_startup_view(request, startup_id):
    startup = get_object_or_404(Startup, pk=startup_id)
    if request.method == 'POST':
        startup_name = startup.name
        startup.delete()
        messages.success(request, f'Startup "{startup_name}" deleted successfully.')
        return redirect('custom_admin:dashboard')
    return render(request, 'custom_admin/delete_startup_confirm.html', {'startup': startup})

@login_required
def blog_event_list_view(request):
    """
    Displays a list of all blogs and events with filtering and sorting options.
    """
    blogs = BlogSection.objects.all().order_by('-created_date')
    events = UpcomingEvent.objects.all().order_by('-created_date')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        blogs = blogs.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__icontains=search_query)
        )
        events = events.filter(description__icontains=search_query)
    
    # Filter by type
    content_type = request.GET.get('type')
    if content_type == 'blog':
        events = None
    elif content_type == 'event':
        blogs = None
    
    context = {
        'blogs': blogs,
        'events': events,
        'search_query': search_query,
        'current_type': content_type,
    }
    return render(request, 'custom_admin/blog_event_list.html', context)

@login_required
def startup_list_view(request):
    """
    Displays a list of all startups with filtering and sorting options.
    """
    startups = Startup.objects.all().order_by('-registrationDate')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        startups = startups.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(industry__icontains=search_query) |
            Q(country__icontains=search_query)
        )
    
    # Filter by industry
    industry = request.GET.get('industry')
    if industry:
        startups = startups.filter(industry__icontains=industry)
    
    # Get unique industries for filter dropdown
    industries = Startup.objects.values_list('industry', flat=True).distinct()
    industry_list = []
    for ind in industries:
        if ind:  # Check if industry is not empty
            industry_list.extend([i.strip() for i in ind.split(',')])
    industry_list = sorted(list(set(industry_list)))  # Remove duplicates and sort
    
    context = {
        'startups': startups,
        'search_query': search_query,
        'current_industry': industry,
        'industries': industry_list,
    }
    return render(request, 'custom_admin/startup_list.html', context)
