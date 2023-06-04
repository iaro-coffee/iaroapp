from django import template

register = template.Library()

@register.filter(name='is_member')
def is_member(user, groupname):
    return user.groups.filter(name=groupname).exists()
