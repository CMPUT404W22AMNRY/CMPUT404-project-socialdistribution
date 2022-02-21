from django.db import models
from django.contrib.auth import get_user_model


class Author(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    github_url = models.CharField(max_length=512, blank=True)
    profile_image_url = models.CharField(max_length=512, blank=True)
