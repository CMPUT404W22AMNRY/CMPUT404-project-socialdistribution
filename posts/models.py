from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

STR_MAX_LENGTH = 512


class Category(models.Model):
    category = models.CharField(max_length=STR_MAX_LENGTH)


class Post(models.Model):
    class ContentType(models.TextChoices):
        MARKDOWN = 'text/markdown', _('text/markdown')
        PLAIN = 'text/plain', _('text/plain')
        BASE64 = 'application/base64', _('application/base64')
        PNG = 'image/png;base64', _('image/png;base64')
        JPG = 'image/jpeg;base64', _('image/jpeg;base64')

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", _('PUBLIC')
        FRIENDS = "FRIENDS", _('PUBLIC')

    title = models.CharField(max_length=STR_MAX_LENGTH)
    description = models.CharField(max_length=STR_MAX_LENGTH)
    content_type = models.CharField(max_length=18, default=ContentType.PLAIN, choices=ContentType.choices)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    date_published = models.DateTimeField(auto_now_add=True)
    unlisted = models.BooleanField()
    categories = models.ManyToManyField(Category)
