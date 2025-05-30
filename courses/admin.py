from django.contrib import admin
from django.db import models
from django.db.models import Sum # Needed for total video duration calculation
from .models import (
    Course, Category, Module, Lesson, VideoLesson, TextLesson, LessonImage,
    Enrollment, LessonProgress, Quiz, Question, Option, QuizAttempt,
    PersonalizedSession
)
from django.contrib.contenttypes.admin import GenericStackedInline # Potentially for polymorphic lessons, but will avoid for simplicity for now.
from django.forms import BaseInlineFormSet # For custom formset validation


# --- Inlines for nested content ---

# Inline for Options (formerly Answer) under Question
class OptionInline(admin.TabularInline):
    model = Option
    extra = 4
    max_num = 4 # Max 4 options per question
    # Ensure is_correct is visible for selection
    fields = ('option_text', 'is_correct')


# Inline for Questions under Quiz
class QuestionInline(admin.StackedInline): # StackedInline for better layout of questions
    model = Question
    extra = 1 # Start with one empty question
    show_change_link = True # Allow navigating to question detail if needed
    inlines = [OptionInline] # Nest options under questions
    fields = ('question_text', 'order')


# Inline for LessonImages under TextLesson
class LessonImageInline(admin.StackedInline):
    model = LessonImage
    extra = 1 # Start with one empty image upload
    fields = ('image', 'caption', 'order')


# Inlines for VideoLesson and TextLesson (content types)
# These will be conditionally displayed on LessonAdmin
class VideoLessonInline(admin.StackedInline):
    model = VideoLesson
    extra = 0 # Only show if Lesson is a video type
    max_num = 1 # One-to-one relationship
    fields = ('video_file', 'video_url', 'duration_seconds')


class TextLessonInline(admin.StackedInline):
    model = TextLesson
    extra = 0 # Only show if Lesson is a text type
    max_num = 1 # One-to-one relationship
    fields = ('content', 'document_file')
    inlines = [LessonImageInline] # Nest lesson images under text lesson


# Inline for Lessons under Module
class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1 # Start with one empty lesson
    show_change_link = True # Essential to navigate to Lesson admin for content (Video/Text)
    fields = ('title', 'description', 'lesson_type', 'order')


# Inline for Modules under Course
class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1  # Start with one empty module
    show_change_link = True  # Allow navigating to module detail if needed
    fields = ('title', 'order')  # Adjust fields as necessary


# --- Admin Classes ---

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)} # Auto-populate slug from name


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'instructor', 'price', 'level', 'duration', 'status', 'enrollments_count', 'created_date') # Updated list_display
    list_filter = ('level', 'status', 'category', 'instructor') # Updated list_filter
    search_fields = ('title', 'description', 'instructor__username', 'category__name') # Search by instructor username and category name
    readonly_fields = ('created_date', 'updated_date')
    inlines = [ModuleInline]
    list_editable = ('status', 'price') # Changed 'is_published' to 'status'
    prepopulated_fields = {'slug': ('title',)} # Auto-populate slug from title
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'category', 'instructor', 'thumbnail', 'level') # Added slug, category, instructor
        }),
        ('Course Details', {
            'fields': ('price', 'duration', 'status') # Changed 'is_published' to 'status'
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_date'),
            'classes': ('collapse',)
        })
    )

    def enrollments_count(self, obj): # Renamed from students_count
        return obj.enrollments.count() # Updated to use .enrollments.count()
    enrollments_count.short_description = 'Enrolled Students'


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'lessons_count')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    ordering = ('course', 'order')
    inlines = [LessonInline] # Keep LessonInline here

    def lessons_count(self, obj):
        return obj.lessons.count()  # Count the number of lessons related to this module
    lessons_count.short_description = 'Number of Lessons'  # Set a short description for the admin display


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'lesson_type', 'order', 'get_duration', 'has_quiz') # Added lesson_type, get_duration
    list_filter = ('module__course', 'module', 'lesson_type') # Added lesson_type to filter
    search_fields = ('title', 'description', 'module__title') # Content is now in TextLesson
    ordering = ('module', 'order')
    raw_id_fields = ('module',) # Useful for selecting module if many exist
    
    # Conditionally display inlines based on lesson_type
    def get_inline_instances(self, request, obj=None):
        inlines = []
        if obj: # Only show inlines if we are editing an existing object
            if obj.lesson_type == 'video':
                inlines.append(VideoLessonInline)
            elif obj.lesson_type == 'text':
                inlines.append(TextLessonInline)
            # You might want to add QuizInline here if a lesson can have a quiz
            # inlines.append(QuizInline) # If Quiz is OneToOne with Lesson, this might be better on QuizAdmin
        return [inline(self.model, self.admin_site) for inline in inlines]

    def get_duration(self, obj):
        if obj.lesson_type == 'video' and hasattr(obj, 'videolesson'):
            return f"{obj.videolesson.duration_seconds // 60}m {obj.videolesson.duration_seconds % 60}s"
        return "N/A"
    get_duration.short_description = 'Duration'

    def has_quiz(self, obj):
        # Quiz is OneToOne with Lesson, so check directly
        return hasattr(obj, 'quiz')
    has_quiz.boolean = True
    has_quiz.short_description = 'Has Quiz'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'passing_score', 'questions_count')
    list_filter = ('passing_score', 'lesson__module__course') # Filter by course
    search_fields = ('title', 'description', 'lesson__title')
    inlines = [QuestionInline] # Keep QuestionInline here
    raw_id_fields = ('lesson',) # Useful for selecting lesson if many exist

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = 'Number of Questions'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'quiz', 'order', 'correct_options_count') # Renamed method
    list_filter = ('quiz__lesson__module__course', 'quiz') # Filter by course and quiz
    search_fields = ('question_text', 'quiz__title')
    inlines = [OptionInline] # Changed from AnswerInline to OptionInline


    def correct_options_count(self, obj): # Renamed from correct_answers_count
        return obj.options.filter(is_correct=True).count() # Updated to use .options
    correct_options_count.short_description = 'Correct Options'


@admin.register(Option) # Registered new Option model
class OptionAdmin(admin.ModelAdmin):
    list_display = ('option_text', 'question', 'is_correct')
    list_filter = ('is_correct', 'question__quiz__lesson__module__course') # Filter by course
    search_fields = ('option_text', 'question__question_text')


@admin.register(Enrollment) # Renamed from CourseEnrollment
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrollment_date', 'is_completed', 'progress_percentage') # Renamed fields
    list_filter = ('is_completed', 'enrollment_date', 'course') # Renamed fields
    search_fields = ('student__email', 'student__username', 'course__title') # Search by student username/email
    readonly_fields = ('enrollment_date', 'completion_date', 'last_accessed') # Added completion_date
    date_hierarchy = 'enrollment_date'

    def progress_percentage(self, obj):
        total_lessons = Lesson.objects.filter(module__course=obj.course).count() # Get total lessons for the course
        completed_lessons = LessonProgress.objects.filter(
            enrollment=obj,
            is_completed=True # Use is_completed
        ).count()
        if total_lessons:
            return f"{(completed_lessons / total_lessons) * 100:.1f}%"
        return "0%"
    progress_percentage.short_description = 'Progress'


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'is_completed', 'completed_date', 'last_accessed') # Renamed 'completed'
    list_filter = ('is_completed', 'completed_date', 'lesson__module__course') # Added course filter
    search_fields = ('enrollment__student__username', 'lesson__title') # Updated search field for student
    readonly_fields = ('last_accessed', 'video_current_time') # Added video_current_time
    date_hierarchy = 'completed_date'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'quiz', 'score', 'passed', 'completed_date')
    list_filter = ('passed', 'completed_date', 'quiz__lesson__module__course') # Filter by course
    search_fields = ('enrollment__student__username', 'quiz__title') # Updated search field for student
    readonly_fields = ('completed_date',)
    date_hierarchy = 'completed_date'


@admin.register(PersonalizedSession)
class PersonalizedSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'instructor', 'course', 'preferred_date', 'status', 'created_date') # Changed student_name to student, added instructor
    list_filter = ('status', 'preferred_date', 'course', 'instructor') # Added instructor to filter
    search_fields = ('student__username', 'student__email', 'instructor__username', 'course__title') # Updated search to use student/instructor username/email
    readonly_fields = ('created_date', 'updated_date')
    date_hierarchy = 'preferred_date'
    fieldsets = (
        ('Student Information', {
            'fields': ('student',) # Changed from student_name, student_email to student ForeignKey
        }),
        ('Session Details', {
            'fields': ('course', 'instructor', 'preferred_date', 'alternate_date', 'meeting_link', 'status') # Added instructor
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_date', 'updated_date'),
            'classes': ('collapse',)
        })
    )

# Removed admin.site.register(Answer) as it's now Option and registered with @admin.register
