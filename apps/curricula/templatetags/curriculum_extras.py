from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Retrieves a value from a dictionary. Converts key to string for robust lookup, especially for JSON-derived dicts."""
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(str(key)) # Ensure key is string for lookup

@register.filter(name='get_item_int_key')
def get_item_int_key(dictionary, key):
    """Retrieves a value from a dictionary using an integer key (less common for JSON keys)."""
    if not isinstance(dictionary, dict):
        return None
    try:
        return dictionary.get(int(key))
    except (ValueError, TypeError):
        return None

@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return ''

@register.filter(name='add_str') # Changed from 'add' to avoid conflict with built-in add if any issue
def add_str(value, arg):
    try:
        return str(value) + str(arg)
    except (ValueError, TypeError):
        return ''

@register.filter(is_safe=True)
def jsonify(obj):
    """Safe filter to convert a Python object to a JSON string."""
    return mark_safe(json.dumps(obj)) 