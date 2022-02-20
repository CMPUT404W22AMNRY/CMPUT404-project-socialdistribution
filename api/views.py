from rest_framework import viewsets
from django.contrib.auth.models import User
from rest_framework import permissions

from api.serializers import AuthorSerializer


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]
