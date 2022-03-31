from markdown_it import MarkdownIt

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def convert_markdown(value):
    md = MarkdownIt('commonmark', {'linkify': True})
    md.enable(["linkify"])
    return md.render(value)
