from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(str(key)) # Ensure key is string for lookup, as semester numbers are strings in JSON

@register.filter(name='get_item_int_key')
def get_item_int_key(dictionary, key):
    """Retrieves a value from a dictionary using an integer key."""
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