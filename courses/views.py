import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db.models import Q, Sum
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from django.http import Http404, JsonResponse
from django.db.models import Count


# IMPORTANT: Replace 'your_app_name' with the actual name of your Django app where models are defined.
from courses.models import (
    Course, Category, Module, Lesson, VideoLesson, TextLesson, LessonImage,
    Enrollment, LessonProgress, Quiz, Question, Option, QuizAttempt
)
logger = logging.getLogger(__name__)  # Add this line

# --- Course Listing View ---
class CourseListView(ListView):
    """
    Displays a list of published courses with search, category, and sorting options.
    """
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 10 # Optional: Add pagination

    def get_queryset(self):
        queryset = super().get_queryset().filter(status='published').select_related('category', 'instructor').order_by('title')

        # Handle search
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(instructor__username__icontains=search_query) # Search by instructor's username
            )

        # Handle category filter
        category_slug = self.request.GET.get('category', '')
        if category_slug and category_slug != 'all':
            queryset = queryset.filter(category__slug=category_slug) # Filter by category slug

        # Handle sorting
        sort_by = self.request.GET.get('sort', 'title')
        if sort_by == 'price_asc': # Explicitly define asc/desc for clarity
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'duration_asc':
            queryset = queryset.order_by('duration')
        elif sort_by == 'duration_desc':
            queryset = queryset.order_by('-duration')
        elif sort_by == 'newest': # Sort by creation date
            queryset = queryset.order_by('-created_date')
        else: # Default to title asc
            queryset = queryset.order_by('title')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_category_slug'] = self.request.GET.get('category', 'all')
        context['sort_by'] = self.request.GET.get('sort', 'title')
        context['categories'] = Category.objects.all().order_by('name') # Pass all categories for filter dropdown
        return context

# --- Course Detail View ---
class CourseDetailView(DetailView):
    """
    Displays a single course's details, modules, and lessons.
    Checks user enrollment status.
    """
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    slug_url_kwarg = 'slug' # Use slug instead of ID for cleaner URLs
    queryset = Course.objects.filter(status='published').prefetch_related(
        'modules__lessons' # Prefetch modules and their lessons
    )

    def get_object(self, queryset=None):
        # Allow fetching by ID or slug if needed, prioritize slug
        if 'slug' in self.kwargs:
            return get_object_or_404(self.get_queryset(), slug=self.kwargs['slug'])
        elif 'pk' in self.kwargs: # Fallback for pk if you still use it in urls
            return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        raise Http404("Course not found.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        is_enrolled = False
        enrollment = None
        if self.request.user.is_authenticated:
            enrollment = Enrollment.objects.filter(student=self.request.user, course=course).first()
            if enrollment:
                is_enrolled = True

        context['is_enrolled'] = is_enrolled
        context['enrollment'] = enrollment # Pass enrollment object for more details if needed
        
        # Calculate total lessons count
        total_lessons_count = Lesson.objects.filter(module__course=course).count()
        context['total_lessons_count'] = total_lessons_count

        # Calculate total video duration for the course
        # Sums duration_seconds from all VideoLessons belonging to this course
        total_video_duration_seconds = VideoLesson.objects.filter(
            lesson__module__course=course
        ).aggregate(total_seconds=Sum('duration_seconds'))['total_seconds'] or 0
        
        # Convert total seconds to hours for display
        total_course_video_duration_hours = round(total_video_duration_seconds / 3600, 1)
        context['total_course_video_duration_hours'] = total_course_video_duration_hours

        
        return context

# --- Course Enrollment View ---
@login_required
def enroll_course(request, slug): # Changed to slug
    """
    Handles enrollment in a course.
    """
    course = get_object_or_404(Course, slug=slug, status='published') # Use slug, ensure published

    if request.method == 'POST':
        # Check if already enrolled
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            messages.info(request, f'You are already enrolled in "{course.title}".')
            return redirect('courses:course_detail', slug=course.slug)

        # Handle free vs. paid enrollment
        if course.price > 0:
            # For paid courses, redirect to checkout
            messages.info(request, f'"{course.title}" is a paid course. Please complete the payment.')
            return redirect('courses:course_checkout', slug=course.slug)
        else:
            # For free courses, directly enroll
            with transaction.atomic(): # Ensure atomicity for database operations
                enrollment = Enrollment.objects.create(
                    student=request.user,
                    course=course,
                    enrollment_date=timezone.now(),
                    is_completed=False
                )
                messages.success(request, f'Successfully enrolled in "{course.title}"!')
                # Optionally, create initial LessonProgress for all lessons if you want to track from start
                # For lesson in course.modules.all().prefetch_related('lessons').values_list('lessons', flat=True):
                #     LessonProgress.objects.create(enrollment=enrollment, lesson_id=lesson)

            return redirect('courses:course_detail', slug=course.slug) # Redirect to course detail after enrollment
    
    # If not a POST request, redirect back to course detail or show an error
    return redirect('courses:course_detail', slug=course.slug)

# --- Lesson Detail View ---
class LessonDetailView(LoginRequiredMixin, DetailView):
    """
    Displays the content of a specific lesson (video or text).
    Updates user's lesson progress and provides relevant content.
    """
    model = Lesson
    template_name = 'courses/lesson_detail.html'
    context_object_name = 'lesson'
    pk_url_kwarg = 'pk' # Use 'pk' as the URL keyword argument for lesson ID

    def get_queryset(self):
        # Prefetch related content for efficiency
        return Lesson.objects.select_related('module__course').prefetch_related(
            'videolesson', 'textlesson__illustrations'
        )

    def get_object(self, queryset=None):
        lesson = super().get_object(queryset)
        # Ensure the user is enrolled in the course this lesson belongs to
        enrollment = get_object_or_404(
            Enrollment,
            student=self.request.user,
            course=lesson.module.course
        )
        self.enrollment = enrollment # Store enrollment for later use in context

        # Create or update lesson progress
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={'last_accessed': timezone.now()} # Set last accessed on creation
        )
        progress.last_accessed = timezone.now() # Always update last accessed
        progress.save()
        self.progress = progress # Store progress for later use in context

        return lesson

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.object
        
        context['progress'] = self.progress
        context['enrollment'] = self.enrollment

        # Pass specific content objects based on lesson type
        if lesson.lesson_type == 'video':
            context['video_content'] = getattr(lesson, 'videolesson', None)
        elif lesson.lesson_type == 'text':
            context['text_content'] = getattr(lesson, 'textlesson', None)
            # Lesson images are prefetched via 'textlesson__illustrations' if you use it in template

        # Get quiz if it exists (OneToOneField means direct access now)
        context['quiz'] = getattr(lesson, 'quiz', None)

        # --- Logic for Previous and Next Lessons ---
        # Get all lessons in the same module, ordered by their 'order'
        all_lessons_in_module = Lesson.objects.filter(
            module=lesson.module
        ).order_by('order')

        previous_lesson = None
        next_lesson = None
        found_current = False

        for l in all_lessons_in_module:
            if l.id == lesson.id:
                found_current = True
                continue  # Skip current lesson
            
            if not found_current:
                previous_lesson = l  # This will be the last lesson before current
            else:
                next_lesson = l  # This will be the first lesson after current
                break  # Found the next, no need to continue

        context['previous_lesson'] = previous_lesson
        context['next_lesson'] = next_lesson
        # --- End Logic for Previous and Next Lessons ---

        return context

# --- Mark Lesson Complete View ---
@login_required
def mark_lesson_complete(request, pk): # Use pk for lesson ID
    """
    Marks a lesson as complete for the enrolled user.
    """
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, pk=pk)
        enrollment = get_object_or_404(
            Enrollment,
            student=request.user,
            course=lesson.module.course
        )
        
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )
        
        if not progress.is_completed: # Use is_completed
            progress.is_completed = True
            progress.completed_date = timezone.now()
            progress.save()
            messages.success(request, f'"{lesson.title}" marked as complete!')
        else:
            messages.info(request, f'"{lesson.title}" is already complete.')
        
        # Redirect to the next lesson or module list
        next_lesson = Lesson.objects.filter(
            module=lesson.module,
            order__gt=lesson.order
        ).order_by('order').first()

        if next_lesson:
            return redirect('courses:lesson_detail', pk=next_lesson.pk)
        else:
            # If no more lessons in this module, go to the module list or course progress
            messages.info(request, f'You have completed all lessons in "{lesson.module.title}".')
            return redirect('courses:module_list', slug=lesson.module.course.slug) # Redirect to module list using course slug

    return redirect('courses:lesson_detail', pk=pk) # Redirect back if not POST

# --- Quiz Detail View ---
class QuizDetailView(LoginRequiredMixin, DetailView):
    """
    Displays a quiz for a lesson.
    """
    model = Quiz
    template_name = 'courses/quiz_detail.html'
    context_object_name = 'quiz'
    pk_url_kwarg = 'pk' # Expects quiz_id as 'pk'

    def get_queryset(self):
        # Prefetch questions and options for efficient rendering
        return Quiz.objects.select_related('lesson__module__course').prefetch_related('questions__options')

    def get_object(self, queryset=None):
        quiz = super().get_object(queryset)
        # Ensure user is enrolled in the course the quiz belongs to
        enrollment = get_object_or_404(
            Enrollment,
            student=self.request.user,
            course=quiz.lesson.module.course
        )
        self.enrollment = enrollment # Store enrollment for later use

        return quiz

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.object
        
        context['lesson'] = quiz.lesson
        context['previous_attempts'] = QuizAttempt.objects.filter(
            enrollment=self.enrollment,
            quiz=quiz
        ).order_by('-completed_date') # Show all attempts, newest first

        return context

# --- Submit Quiz View ---
@login_required
def submit_quiz(request, pk): # Changed to quiz_id as pk
    """
    Processes quiz submissions, calculates score, and records attempt.
    """
    if request.method == 'POST':
        quiz = get_object_or_404(Quiz, pk=pk)
        enrollment = get_object_or_404(
            Enrollment,
            student=request.user,
            course=quiz.lesson.module.course
        )

        correct_answers_count = 0
        total_questions = quiz.questions.count()

        if total_questions == 0:
            messages.warning(request, "This quiz has no questions.")
            return redirect('courses:quiz_detail', pk=quiz.pk)

        for question in quiz.questions.all():
            # Get selected option ID from POST data
            selected_option_id = request.POST.get(f'question_{question.id}')
            if selected_option_id:
                try:
                    # Use Option model (renamed from Answer)
                    selected_option = Option.objects.get(id=selected_option_id, question=question)
                    if selected_option.is_correct:
                        correct_answers_count += 1
                except Option.DoesNotExist:
                    # Handle cases where an invalid option ID is submitted
                    pass

        score = (correct_answers_count / total_questions) * 100
        passed = score >= quiz.passing_score

        # Create quiz attempt
        QuizAttempt.objects.create(
            enrollment=enrollment,
            quiz=quiz,
            score=score,
            passed=passed,
            completed_date=timezone.now()
        )

        if passed:
            messages.success(request, f'Congratulations! You passed the quiz with a score of {score:.2f}%.')
            # Optionally mark the lesson as complete if quiz is passed
            lesson_progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=quiz.lesson
            )
            if not lesson_progress.is_completed:
                lesson_progress.is_completed = True
                lesson_progress.completed_date = timezone.now()
                lesson_progress.save()
                messages.info(request, f'Lesson "{quiz.lesson.title}" marked as complete after passing the quiz.')
        else:
            messages.warning(request, f'You scored {score:.2f}%. Required passing score is {quiz.passing_score}%. Please try again.')

        return redirect('courses:quiz_detail', pk=quiz.pk) # Redirect back to quiz detail to show results/previous attempts

    return redirect('courses:quiz_detail', pk=pk) # Redirect back if not POST

# --- Course Checkout (Placeholder for Payment Integration) ---
@login_required
def course_checkout(request, slug): # Use slug
    """
    Placeholder view for handling course checkout.
    This is where you'd integrate payment gateways (e.g., M-Pesa, Stripe).
    """
    course = get_object_or_404(Course, slug=slug, status='published')

    # Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.warning(request, "You are already enrolled in this course.")
        return redirect('courses:course_detail', slug=course.slug)

    context = {
        'course': course,
        # Add any payment-related context here (e.g., payment form, M-Pesa stk push details)
    }
    return render(request, 'courses/course_checkout.html', context)

@login_required
def process_payment(request, slug):
    """
    Simulated/Placeholder view for processing payment and enrolling.
    In a real app, this would be a webhook or callback from your payment gateway.
    """
    try:
        # Try to get course by slug first
        course = get_object_or_404(Course, slug=slug, status='published')
    except Course.DoesNotExist:
        # If not found by slug, try by ID
        try:
            course = get_object_or_404(Course, id=slug, status='published')
        except (ValueError, Course.DoesNotExist):
            raise Http404("Course not found")

    if request.method == 'POST':
        # For testing purposes, always set payment as successful
        payment_successful = True

        if payment_successful:
            with transaction.atomic():
                enrollment, created = Enrollment.objects.get_or_create(
                    student=request.user,
                    course=course,
                    defaults={
                        'enrollment_date': timezone.now(),
                        'is_completed': False,
                        'last_accessed': timezone.now()
                    }
                )
                if created:
                    messages.success(request, f'Payment successful! You are now enrolled in "{course.title}".')
                else:
                    messages.info(request, f'You were already enrolled in "{course.title}" and payment was confirmed.')
            return redirect('courses:course_detail', slug=course.slug)
        else:
            messages.error(request, 'Payment failed. Please try again or contact support.')
            return redirect('courses:course_checkout', slug=course.slug)

    return redirect('courses:course_detail', slug=course.slug)

# --- Module List View (within an enrolled course) ---
@login_required
def module_list(request, slug): # Use slug for course
    """
    Displays the modules and lessons for an enrolled course, including progress.
    """
    course = get_object_or_404(Course, slug=slug, status='published')
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=course
    )
    
    # Get all modules with their lessons, prefetch related content for lessons
    modules = course.modules.prefetch_related(
        'lessons__videolesson',
        'lessons__textlesson__illustrations' # Ensure illustrations are fetched
    ).all()
    
    # Get completed lessons for this enrollment
    completed_lessons_ids = LessonProgress.objects.filter(
        enrollment=enrollment,
        is_completed=True # Use is_completed
    ).values_list('lesson_id', flat=True)
    
    # Calculate overall course progress
    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_count = len(completed_lessons_ids)
    progress_percentage = (completed_count / total_lessons * 100) if total_lessons > 0 else 0
    
    # For SVG circle animation (client-side calculation might be better)
    # progress_offset = 364.4 * (1 - progress_percentage / 100)
    
    # Calculate time spent (sum of durations of completed lessons)
    # Note: lesson__duration needs to come from VideoLesson.duration_seconds
    # This requires more complex aggregation if text lessons don't have duration
    # For simplicity, we'll sum video durations for completed lessons.
    total_video_duration_completed = LessonProgress.objects.filter(
        enrollment=enrollment,
        is_completed=True,
        lesson__lesson_type='video'
    ).aggregate(
        total_seconds=Sum('lesson__videolesson__duration_seconds')
    )['total_seconds'] or 0
    
    time_spent_hours = round(total_video_duration_completed / 3600, 1) # Convert seconds to hours
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'modules': modules,
        'completed_lessons_ids': completed_lessons_ids,
        'progress_percentage': progress_percentage,
        # 'progress_offset': progress_offset, # Use in template for SVG
        'total_lessons': total_lessons,
        'time_spent_hours': time_spent_hours,
    }
    return render(request, 'courses/module_list.html', context)


# --- Course Progress Overview ---
@login_required
def course_progress(request, slug):
    """
    Displays detailed overview of user's progress in a specific course.
    """
    try:
        # Get course and enrollment
        course = get_object_or_404(Course, slug=slug, status='published')
        enrollment = get_object_or_404(
            Enrollment,
            student=request.user,
            course=course
        )
        
        # Get all lessons with optimized queries
        all_lessons = Lesson.objects.filter(module__course=course).select_related(
            'videolesson', 'textlesson', 'quiz'
        ).prefetch_related('module').order_by('module__order', 'order')

        # Prefetch lesson progresses in one query
        lesson_progresses = {
            progress.lesson_id: progress 
            for progress in LessonProgress.objects.filter(enrollment=enrollment)
        }

        # Prepare lessons data
        lessons_with_status = []
        total_lessons_count = all_lessons.count()
        completed_lessons_count = 0
        
        for lesson in all_lessons:
            progress = lesson_progresses.get(lesson.id)
            is_completed = progress.is_completed if progress else False
            completed_lessons_count += 1 if is_completed else 0
            
            lessons_with_status.append({
                'lesson': lesson,
                'is_completed': is_completed,
                'last_accessed': progress.last_accessed if progress else None,
                'completed_date': progress.completed_date if progress else None,
                'video_current_time': progress.video_current_time if progress else 0.0,
                'video_content': getattr(lesson, 'videolesson', None),
                'text_content': getattr(lesson, 'textlesson', None),
                'quiz': getattr(lesson, 'quiz', None),
                'module_title': lesson.module.title
            })

        # Calculate progress
        progress_percentage = round(
            (completed_lessons_count / total_lessons_count * 100)
        ) if total_lessons_count > 0 else 0

        # Get quiz attempts
        quiz_attempts = QuizAttempt.objects.filter(
            enrollment=enrollment,
            quiz__lesson__module__course=course
        ).select_related('quiz__lesson').order_by('-completed_date')

        context = {
            'course': course,
            'enrollment': enrollment,
            'progress_percentage': progress_percentage,
            'completed_lessons': completed_lessons_count,
            'total_lessons': total_lessons_count,
            'lessons': lessons_with_status,  # Changed from lessons_with_status for consistency
            'quiz_attempts': quiz_attempts,
        }
        
        return render(request, 'courses/course_progress.html', context)

    except Http404:
        # Provide specific error messages
        if not Course.objects.filter(slug=slug).exists():
            raise Http404(f"No course found with slug: '{slug}'")
        elif not Course.objects.filter(slug=slug, status='published').exists():
            raise Http404(f"Course '{slug}' exists but isn't published")
        elif not Enrollment.objects.filter(student=request.user, course__slug=slug).exists():
            raise Http404(f"You are not enrolled in course '{slug}'")
        raise
        
    except Exception as e:
        logger.error(f"Error in course_progress view: {str(e)}")
        raise Http404("Could not load course progress")

# --- Additional API-like views for client-side progress tracking ---
@login_required
def update_video_progress(request, lesson_id):
    """
    API endpoint to update video progress (current time).
    Expected POST data: {'currentTime': float_value}
    """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        lesson = get_object_or_404(Lesson, pk=lesson_id, lesson_type='video')
        enrollment = get_object_or_404(
            Enrollment,
            student=request.user,
            course=lesson.module.course
        )
        
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )
        
        try:
            current_time = float(request.POST.get('currentTime', 0.0))
            if current_time >= 0:
                progress.video_current_time = current_time
                progress.last_accessed = timezone.now()
                progress.save()
                return JsonResponse({'status': 'success', 'currentTime': current_time})
            return JsonResponse({'status': 'error', 'message': 'Invalid time'}, status=400)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid data format'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def personalized_courses_view(request):
    user = request.user
    
    # Get IDs of courses the user is already enrolled in
    enrolled_course_ids = Enrollment.objects.filter(student=user).values_list('course_id', flat=True)

    # Get popular courses the user hasn't enrolled in, ordered by number of enrollments
    recommended_courses = (
        Course.objects
        .exclude(id__in=enrolled_course_ids)
        .annotate(enrollment_count=Count('enrollments'))  # annotate with enrollment count
        .order_by('-enrollment_count')[:5]  # top 5 popular
    )

    context = {
        'recommended_courses': recommended_courses
    }
    return render(request, 'courses/personalized.html', context)

# Don't forget to add JsonResponse to your imports if you use update_video_progress

