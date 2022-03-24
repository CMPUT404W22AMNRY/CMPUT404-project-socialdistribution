from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

import requests

import mimetypes


def is_url_valid(url: str) -> bool:
    validate = URLValidator()
    try:
        validate(url)
    except ValidationError:
        return False

    return True


# def is_url_valid_image(url: str) -> bool:
#     return is_url_valid(url) and is_url_image(url)


# # inspired by MattoTodd on StackOverflow https://stackoverflow.com/a/10543969
# def is_url_image(url: str) -> bool:
#     mimetype = mimetypes.guess_type(url)
#     return (mimetype and mimetype[0] and mimetype[0].startswith('image'))

def is_url_valid_image(url: str) -> bool:
    h = requests.head(url)
    header = h.headers
    content_type = header.get('content-type')
    return content_type.startswith('image')
