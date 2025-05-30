from django import forms
from django.forms import inlineformset_factory

# IMPORTANT: Replace 'your_app_name' with the actual name of your Django app where models are defined.
# For example, if your models are in 'lms_app/models.py', then use 'lms_app.models'.
from courses.models import Course, Module, Lesson, VideoLesson, TextLesson, LessonImage, Category

# --- Course Forms ---
class CourseForm(forms.ModelForm):
    """
    Form for creating and updating Course objects.
    Includes fields for basic course information.
    """
    class Meta:
        model = Course
        fields = [
            'title', 'slug', 'description', 'category', 'instructor',
            'price', 'duration', 'thumbnail', 'level', 'status'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'slug': forms.TextInput(attrs={'placeholder': 'Auto-generated or custom slug'}),
        }
        help_texts = {
            'slug': 'A unique, URL-friendly identifier for the course. Leave blank to auto-generate.',
            'thumbnail': 'Upload a cover image for your course.',
            'status': 'Set to "Published" to make the course visible to students.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add a placeholder for the instructor field if it's empty
        if 'instructor' in self.fields:
            self.fields['instructor'].empty_label = "Select an Instructor"
        # Populate category choices
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['category'].empty_label = "Select a Category"

        # You might want to filter instructors to only show users marked as instructors
        # from users.models import User # Make sure to import User if not already
        # self.fields['instructor'].queryset = User.objects.filter(is_instructor=True) # Assuming 'is_instructor' field exists on your User model


# --- Module Forms and Formset ---
class ModuleForm(forms.ModelForm):
    """
    Form for creating and updating Module objects.
    """
    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'order': forms.NumberInput(attrs={'placeholder': 'Order in course'}),
        }
        help_texts = {
            'order': 'The sequential order of this module within the course.',
        }

# Inline formset for Modules related to a Course
ModuleFormSet = inlineformset_factory(
    Course,
    Module,
    form=ModuleForm,
    extra=1, # Number of empty forms to display
    can_delete=True,
    fields=['title', 'description', 'order'],
    # You might want to limit the maximum number of modules
    # max_num=10,
)


# --- Lesson Forms and Formsets ---
class LessonForm(forms.ModelForm):
    """
    Base form for creating and updating Lesson objects.
    This form handles common lesson fields and the lesson_type.
    """
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'lesson_type', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'order': forms.NumberInput(attrs={'placeholder': 'Order in module'}),
        }
        help_texts = {
            'lesson_type': 'Choose whether this lesson is video-based or text-based.',
            'order': 'The sequential order of this lesson within its module.',
        }

class VideoLessonForm(forms.ModelForm):
    """
    Form for creating and updating VideoLesson content.
    """
    class Meta:
        model = VideoLesson
        fields = ['video_file', 'video_url', 'duration_seconds']
        help_texts = {
            'video_file': 'Upload a video file directly.',
            'video_url': 'Or provide a URL from an external video hosting service (e.g., YouTube, Vimeo).',
            'duration_seconds': 'Duration of the video in seconds.',
        }

class TextLessonForm(forms.ModelForm):
    """
    Form for creating and updating TextLesson content.
    Includes fields for rich text content and optional document uploads.
    """
    class Meta:
        model = TextLesson
        fields = ['content', 'document_file']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}), # Use a larger textarea for rich text
        }
        help_texts = {
            'content': 'Enter the main text content for this lesson. You can use HTML for rich formatting.',
            'document_file': 'Upload supplementary documents (PDF, Word, TXT) for this lesson.',
        }

class LessonImageForm(forms.ModelForm):
    """
    Form for uploading images associated with TextLessons.
    """
    class Meta:
        model = LessonImage
        fields = ['image', 'caption', 'order']
        help_texts = {
            'image': 'Upload an image to illustrate the text lesson.',
            'caption': 'A brief description of the image.',
            'order': 'The display order of this image within the lesson.',
        }

# Inline formsets for Lesson content types
# These will be conditionally rendered/used in the view based on Lesson.lesson_type

# Formset for Lessons related to a Module
LessonFormSet = inlineformset_factory(
    Module,
    Lesson,
    form=LessonForm,
    extra=1,
    can_delete=True,
    fields=['title', 'description', 'lesson_type', 'order'],
    # max_num=10,
)

# Formset for VideoLesson content related to a Lesson
VideoLessonContentFormSet = inlineformset_factory(
    Lesson,
    VideoLesson,
    form=VideoLessonForm,
    extra=0, # Only show if lesson_type is 'video'
    can_delete=False, # VideoLesson is OneToOne, so it's managed by Lesson
    max_num=1, # Only one VideoLesson per Lesson
)

# Formset for TextLesson content related to a Lesson
TextLessonContentFormSet = inlineformset_factory(
    Lesson,
    TextLesson,
    form=TextLessonForm,
    extra=0, # Only show if lesson_type is 'text'
    can_delete=False, # TextLesson is OneToOne, so it's managed by Lesson
    max_num=1, # Only one TextLesson per Lesson
)

# Formset for LessonImages related to a TextLesson
LessonImageFormSet = inlineformset_factory(
    TextLesson,
    LessonImage,
    form=LessonImageForm,
    extra=1, # Allow adding multiple images
    can_delete=True,
    fields=['image', 'caption', 'order'],
)

