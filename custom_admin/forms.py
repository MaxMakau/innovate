from django import forms
from courses.models import Course, Module, Lesson, Question, Quiz, VideoLesson, TextLesson, Option
from services.models import BlogSection, UpcomingEvent
from startups.models import Startup

class StartupForm(forms.ModelForm):
    class Meta:
        model = Startup
        fields = ['name', 'image', 'team_size', 'funding', 'description', 'industry', 'country', 'registrationDate']

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'slug', 'description', 'category', 'instructor',
            'price', 'duration', 'thumbnail', 'level', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'instructor': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'slug': 'A unique identifier for the course URL (e.g., "python-basics")',
            'price': 'Set to 0 for free courses',
            'duration': 'Duration in weeks',
        }

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = '__all__'

class VideoLessonForm(forms.ModelForm):
    class Meta:
        model = VideoLesson
        fields = ['video_file', 'video_url', 'duration_seconds']

class TextLessonForm(forms.ModelForm):
    class Meta:
        model = TextLesson
        fields = ['content', 'document_file']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6}),
        }

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'passing_score']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3}),
        }

class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['option_text', 'is_correct']

class BlogEventForm(forms.Form):
    TYPE_CHOICES = [
        ('blog', 'Blog'),
        ('event', 'Event'),
    ]


    
    type = forms.ChoiceField(choices=TYPE_CHOICES, widget=forms.RadioSelect)
    title = forms.CharField(max_length=200, required=False)
    content = forms.CharField(widget=forms.Textarea, required=False)
    author = forms.CharField(max_length=100, required=False)
    description = forms.CharField(widget=forms.Textarea, required=False)
    image = forms.ImageField(required=False)


