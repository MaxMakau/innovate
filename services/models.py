from django.db import models

class BlogSection(models.Model):
    title = models.CharField(max_length=200)
    content = models.CharField(max_length=300)
    author = models.CharField(max_length=100)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='blogs/', blank=True, null=True)
    
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_date']

        
class UpcomingEvent(models.Model):
    description = models.TextField()
    image = models.ImageField(upload_to='events/')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['description']

class Achievement(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='achievements/', blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Startup(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='startups/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_date']