import re
from markdown_it import MarkdownIt

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def convert_markdown(value):
    md = MarkdownIt('commonmark')
    return md.render(value)


# https://stackoverflow.com/questions/53980097/removing-markup-links-in-text
@register.filter
@stringfilter
def convert_markdown_no_links(value):
    md = MarkdownIt('commonmark')
    md.disable('link')
    return re.sub(r"\[(.+)\]\(.+\)", r"\1", md.render(value))
