import json

from django import template
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()


@register.filter(name="to_json")
def to_json(value):
    return json.dumps(value, cls=DjangoJSONEncoder)
