import os
import json
from django import template

register = template.Library()

@register.filter
def file_exists(filepath):
    return os.path.exists(filepath)

@register.filter
def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except:
        return {}
