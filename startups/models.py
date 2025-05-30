from django.db import models

class Startup(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='startups/')
    team_size = models.PositiveIntegerField()
    funding = models.CharField(max_length=50) 
    description = models.TextField()
    industry = models.CharField(max_length=255, help_text="Comma-separated industry tags, e.g., AI, Fintech, Medtech", blank=True)
    country = models.CharField(max_length=20)
    registrationDate = models.CharField(max_length=10, help_text="Enter in MM/YYYY format")  # Change to CharField

   
    def __str__(self):
        return self.name
