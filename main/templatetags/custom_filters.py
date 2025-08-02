from django import template
from django.utils.html import strip_tags
from django.template.defaultfilters import truncatewords

register = template.Library()

@register.filter(name='split')
def split(value, key):
    """Split a string by the given key"""
    if not value:
        return []
    return value.split(key)

@register.filter(name='trim')
def trim(value):
    """Remove leading and trailing whitespace"""
    if not value:
        return value
    return str(value).strip()

@register.filter(name='truncatewords_html')
def truncatewords_html(value, arg):
    """Truncate HTML content while preserving tags"""
    return truncatewords(strip_tags(value), arg)
