from django import template

from bookmarks import utils

register = template.Library()


@register.simple_tag(takes_context=True)
def update_query_string(context, **kwargs):
    query = context.request.GET.copy()

    # Replace query params with the ones from tag parameters
    for key in kwargs:
        query.__setitem__(key, kwargs[key])

    return query.urlencode()


@register.simple_tag(takes_context=True)
def append_query_param(context, **kwargs):
    query = context.request.GET.copy()

    # Append to or create query param
    for key in kwargs:
        tags = []
        if query.__contains__(key):
            value = query.__getitem__(key) + ' '
            tags = query.__getitem__(key).split(' ')
        else:
            value = ''
        if kwargs[key] in tags:
            while kwargs[key] in tags:
                tags.pop(tags.index(kwargs[key]))
            if len(tags) == 0:
                value = ''
            else:
                value = " ".join(tags)
        else:
            value = value + kwargs[key]
        if value == '':
            query.__delitem__(key)
        else:
            query.__setitem__(key, value)

    return query.urlencode()


@register.filter(name='hash_tag')
def hash_tag(tag_name):
    return '#' + tag_name


@register.filter(name='first_char')
def first_char(text):
    return text[0]


@register.filter(name='remaining_chars')
def remaining_chars(text, index):
    return text[index:]


@register.filter(name='humanize_absolute_date')
def humanize_absolute_date(value):
    if value in (None, ''):
        return ''
    return utils.humanize_absolute_date(value)


@register.filter(name='humanize_relative_date')
def humanize_relative_date(value):
    if value in (None, ''):
        return ''
    return utils.humanize_relative_date(value)
