import uuid
from django.db import models
from django.forms import ValidationError
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from socialdistribution.storage import ImageStorage
from lib.url import is_url_valid_image

STR_MAX_LENGTH = 512


class Category(models.Model):
    category = models.CharField(max_length=STR_MAX_LENGTH)


class ContentType(models.TextChoices):
    MARKDOWN = 'text/markdown', _('Commonmark')
    PLAIN = 'text/plain', _('Plaintext')
    BASE64 = 'application/base64', _('Base64Encoded')
    PNG = 'image/png;base64', _('PNG')
    JPG = 'image/jpeg;base64', _('JPEG')


def img_content_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4().hex, ext)
    return filename


class Post(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC"
        FRIENDS = "FRIENDS"

    title = models.CharField(max_length=STR_MAX_LENGTH)
    description = models.CharField(max_length=STR_MAX_LENGTH)
    content_type = models.CharField(max_length=18, default=ContentType.PLAIN, choices=ContentType.choices)
    visibility = models.CharField(max_length=7, default=Visibility.PUBLIC, choices=Visibility.choices)
    content = models.TextField()
    img_content = models.ImageField(
        null=True,
        blank=True,
        storage=ImageStorage(),
        upload_to=img_content_filename,
        verbose_name='Image')
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    original_author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='+', editable=False)
    date_published = models.DateTimeField(auto_now_add=True)
    unlisted = models.BooleanField()
    categories = models.ManyToManyField(Category, blank=True)

    def clean(self):
        # Ensure that either the content is a link to image, or they uploaded one
        if self.content_type == ContentType.PNG or self.content_type == ContentType.JPG:
            if (not self.img_content and not is_url_valid_image(self.content)):
                raise ValidationError(
                    _('You must upload an image or link to a valid image url in the \'Content\' field.'))

    def get_absolute_url(self):
        return reverse('posts:detail', kwargs={'pk': self.id})

    def save(self, *args, **kwargs):
        self.clean()
        return super(Post, self).save(*args, **kwargs)


class Comment(models.Model):
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    comment = models.TextField()
    content_type = models.CharField(max_length=18, default=ContentType.PLAIN, choices=ContentType.choices)
    date_published = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class Like(models.Model):
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class RemoteLike(models.Model):
    author_url = models.CharField(max_length=STR_MAX_LENGTH)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class CommentLike(models.Model):
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)


class RemoteComment(models.Model):
    author_url = models.CharField(max_length=STR_MAX_LENGTH)
    comment = models.TextField()
    content_type = models.CharField(max_length=18, default=ContentType.PLAIN, choices=ContentType.choices)
    date_published = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
