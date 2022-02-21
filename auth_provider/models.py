from django.db import models
from django.contrib.auth import get_user_model


class Author(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)

    class Meta:
        permissions = [
            ("use_app", "Can access the current app"),
        ]
