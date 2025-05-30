from django import template
import re

register = template.Library()

@register.filter
def youtube_embed_url(value):
    """
    Converts a standard YouTube watch URL to an embed URL.
    Example:
    https://www.youtube.com/watch?v=dQw4w9WgXcQ
    becomes
    https://www.youtube.com/embed/dQw4w9WgXcQ
    """
    if not value:
        return ""
    
    # Regex to extract YouTube video ID
    # Handles watch?v=, youtu.be/, embed/
    match = re.search(r'(?:https?:\/\/)?(?:www\.)?(?:m\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=|embed\/|v\/|)([\w-]{11})(?:\S+)?', value)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/embed/{video_id}"
    return value # Return original if not a valid YouTube URL

@register.filter
def ends_with(value, arg):
    """
    Checks if a string ends with a given suffix.
    Usage: {{ some_string|ends_with:".pdf" }}
    """
    return str(value).endswith(str(arg))