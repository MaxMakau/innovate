# Generated by Django 5.0.2 on 2025-05-30 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogsection',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='blogs/'),
        ),
    ]
