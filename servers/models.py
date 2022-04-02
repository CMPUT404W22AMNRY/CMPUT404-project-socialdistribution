from typing import Dict
from django.db import models
from requests.auth import HTTPBasicAuth
import requests
import requests_cache

STR_MAX_LENGTH = 512

requests_cache.install_cache(expire_after=180)  # Cache GET and HEAD results for 180 seconds


class Server(models.Model):
    service_address = models.CharField(max_length=STR_MAX_LENGTH)
    username = models.CharField(max_length=STR_MAX_LENGTH)
    password = models.CharField(max_length=STR_MAX_LENGTH)

    def get(self, endpoint: str, params: Dict[str, str] = []) -> requests.Response:
        full_endpoint = self.service_address + endpoint
        return requests.get(full_endpoint, params, auth=HTTPBasicAuth(self.username, self.password))
