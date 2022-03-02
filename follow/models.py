import re
from urllib import request
from django.db import models
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from follow.signals import (
    request_create,
    request_reject,
    request_cancel,
    request_accept,
)

# Create your models here.

class AlreadyExistsError(IntegrityError):
    pass

