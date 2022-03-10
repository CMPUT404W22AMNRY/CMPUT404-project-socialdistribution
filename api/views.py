from rest_framework import viewsets
from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import action

from api.serializers import AuthorSerializer #, ImageSerializer
from api.util import page_number_pagination_class_factory


class AuthorViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'authors')])

    queryset = get_user_model().objects.filter(is_active=True, is_staff=False).order_by('id')
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    @action(
        methods=['get'], 
        detail=True,         
        url_path='posts',
        url_name='posts'
    )
    def Posts(self, request, pk=None):
        # TODO: Implement /authors/{AUTHOR_ID}/POSTS/
        return Response({})

# class ImageViewSet(viewsets.ModelViewSet):
#     renderer_classes = [JSONRenderer]

#     # queryset = get_user_model().objects.filter(is_active=True, is_staff=False).order_by('id')
#     serializer_class = ImageSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     http_method_names = ['get']
#
