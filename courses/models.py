# Assuming 'users.models.User' is your custom user model
from django.db import models
from users.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, help_text="A unique identifier for the category, used in URLs.")

    class Meta:
        verbose_name_plural = "Categories" # Fix for Django Admin pluralization

    def __str__(self):
        return self.name

class Course(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text="A unique identifier for the course, used in URLs.")
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_taught') # Assuming User can be an instructor
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00) # 0 for free courses
    duration = models.PositiveIntegerField(help_text="Duration in weeks", default=0) # Changed to PositiveIntegerField
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True) # Added null=True
    level = models.CharField(max_length=20, choices=[
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced')
    ], default='BEGINNER') # Added default
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published') # Replaced is_published
    # Removed students ManyToManyField as CourseEnrollment handles it

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True) # Made blank=True
    order = models.PositiveIntegerField(default=0) # Changed to PositiveIntegerField and added default
    
    class Meta:
        ordering = ['order']
        unique_together = [['course', 'order']]

    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @classmethod
    def get_next_order(cls, course):
        """Get the next available order number for a module in a course."""
        last_module = cls.objects.filter(course=course).order_by('-order').first()
        return (last_module.order + 1) if last_module else 0

class Lesson(models.Model):
    LESSON_TYPES = [
        ('video', 'Video Lesson'),
        ('text', 'Text Lesson'),
    ]
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True) # Added description
    lesson_type = models.CharField(max_length=10, choices=LESSON_TYPES) # To distinguish content type
    order = models.PositiveIntegerField(default=0) # Changed to PositiveIntegerField and added default
    duration = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)  # duration in hours

    class Meta:
        ordering = ['order']
        unique_together = [['module', 'order']]

    def __str__(self):
        return self.title
    
    @classmethod
    def get_next_order(cls, module):
        """Get the next available order number for a lesson in a module."""
        last_lesson = cls.objects.filter(module=module).order_by('-order').first()
        return (last_lesson.order + 1) if last_lesson else 0

class VideoLesson(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, primary_key=True)
    video_file = models.FileField(upload_to='video_lessons/', blank=True, null=True) # For direct uploads
    video_url = models.URLField(blank=True, null=True) # For external platforms (YouTube, Vimeo)
    duration_seconds = models.PositiveIntegerField(default=0, help_text="Duration in seconds") # Changed to seconds for granularity

    def __str__(self):
        return f"Video: {self.lesson.title}"

class TextLesson(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, primary_key=True)
    content = models.TextField() # This will hold the rich text content
    document_file = models.FileField(upload_to='lesson_documents/', blank=True, null=True, help_text="Upload PDF, Word, or text files for the lesson.") 

    def __str__(self):
        return f"Text: {self.lesson.title}"

class LessonImage(models.Model): # For graphical illustrations in text lessons
    text_lesson = models.ForeignKey(TextLesson, on_delete=models.CASCADE, related_name='illustrations')
    image = models.ImageField(upload_to='lesson_illustrations/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.text_lesson.lesson.title} - {self.caption[:20]}"

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments') # Renamed user to student
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True) # Renamed enrolled_date
    is_completed = models.BooleanField(default=False) # Renamed completed
    completion_date = models.DateTimeField(null=True, blank=True) # Added completion date
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"

class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progresses') # Updated FK
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False) # Renamed completed
    completed_date = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    video_current_time = models.FloatField(default=0.0) # For video lessons, to resume playback

    class Meta:
        unique_together = ('enrollment', 'lesson')

    def __str__(self):
        return f"{self.enrollment.student.username} - {self.lesson.title} Progress"

class Quiz(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz') # Changed to OneToOneField
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True) # Made blank=True
    passing_score = models.PositiveIntegerField(default=70) # Changed to PositiveIntegerField

    class Meta:
        verbose_name_plural = "Quizzes" # Fix for Django Admin pluralization

    def __str__(self):
        return f"Quiz for {self.lesson.title}"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    order = models.PositiveIntegerField(default=0) # Changed to PositiveIntegerField and added default

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question_text[:75] # Display first 75 chars

class Option(models.Model): # Renamed from Answer
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options') # Renamed related_name
    option_text = models.CharField(max_length=255) # Renamed answer_text
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.option_text

class QuizAttempt(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='quiz_attempts') # Updated FK, added related_name
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0) # Changed to PositiveIntegerField
    completed_date = models.DateTimeField(auto_now_add=True)
    passed = models.BooleanField(default=False)

    class Meta:
        # If you want to allow multiple attempts per quiz per enrollment, remove unique_together
        # unique_together = ('enrollment', 'quiz')
        pass 

    def __str__(self):
        return f"{self.enrollment.student.username} - {self.quiz.title} Attempt ({self.score}%)"

class PersonalizedSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personalized_sessions') # Linked to User model
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions_led') # Optional: Link to instructor
    preferred_date = models.DateTimeField()
    alternate_date = models.DateTimeField(null=True, blank=True) # Made optional
    meeting_link = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('CONFIRMED', 'Confirmed'), 
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled')
        ],
        default='PENDING'
    )
    notes = models.TextField(blank=True, null=True) # Added null=True
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session for {self.student.username} on {self.course.title}"

    class Meta:
        ordering = ['-preferred_date']

