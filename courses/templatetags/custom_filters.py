# courses/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def floordiv(value, arg):
    return value // arg

@register.filter
def mod(value, arg):
    return value % arg

@register.filter
def split(value, arg):
    return value.split(arg)