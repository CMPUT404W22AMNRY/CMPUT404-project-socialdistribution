from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

import requests

import mimetypes

from urllib import parse


def is_url_valid(url: str) -> bool:
    validate = URLValidator()
    try:
        validate(url)
    except ValidationError:
        return False

    return True


# inspired by MattoTodd on StackOverflow https://stackoverflow.com/a/10543969
def is_url_image(url: str) -> bool:
    mimetype = mimetypes.guess_type(url)
    return (mimetype and mimetype[0] and mimetype[0].startswith('image'))


def is_url_valid_image(url: str) -> bool:
    # check the returned returned content type
    head = requests.head(url)
    if head.headers.get('content-type').startswith('image'):
        return True

    if head.status_code == 403:
        # if HEAD isn't allowed, try a GET
        get = requests.get(url)
        return get.headers.get('content-type').startswith('image')

    return False


def get_github_user_from_url(url: str):
    parsed_url = parse.urlparse(url)
    if parsed_url.scheme == 'http' or parsed_url.scheme == 'https':
        if 'github' in parsed_url.hostname and parsed_url.path:
            return parsed_url.path.strip('/')
    return None
