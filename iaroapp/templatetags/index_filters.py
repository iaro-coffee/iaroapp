from django import template

register = template.Library()


@register.filter(name="index")
def index(indexable, i):
    return indexable[i - 1]  # start at 1


@register.filter(name="reverse_index")
def reverse_index(indexable, i):
    return indexable[-i]  # start at 1
