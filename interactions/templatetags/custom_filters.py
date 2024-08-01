from django import template

register = template.Library()


@register.filter(name="https")
def https(value):
    if isinstance(value, str):
        return value.replace("http://", "https://")
    return value
