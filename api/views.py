from rest_framework import viewsets
from django.contrib.auth.models import User
from rest_framework import permissions

from api.serializers import AuthorSerializer
from api.util import getNamedRenderer


class AuthorViewSet(viewsets.ModelViewSet):
    renderer_classes = [getNamedRenderer('authors')]

    queryset = User.objects.all().order_by('id')
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']
