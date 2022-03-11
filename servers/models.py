from django.db import models

STR_MAX_LENGTH = 512


class Server(models.Model):
    service_address = models.CharField(max_length=STR_MAX_LENGTH)
    username = models.CharField(max_length=STR_MAX_LENGTH)
    password = models.CharField(max_length=STR_MAX_LENGTH)
