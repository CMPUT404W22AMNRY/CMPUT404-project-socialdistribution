from rest_framework import viewsets
from django.contrib.auth.models import User
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer

from api.serializers import AuthorSerializer
from api.util import page_number_pagination_class_factory


class AuthorViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'authors')])

    queryset = User.objects.all().order_by('id')
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']
