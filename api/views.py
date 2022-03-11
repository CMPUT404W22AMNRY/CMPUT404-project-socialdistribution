import base64
import os
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import action

from posts.models import Post, ContentType

from api.serializers import AuthorSerializer, PostSerializer
from api.util import page_number_pagination_class_factory


class AuthorViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'authors')])

    queryset = get_user_model().objects.filter(is_active=True, is_staff=False).order_by('id')
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']


class PostViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'posts')])

    # TODO: set up the posts model
    queryset = Post.objects.order_by('id')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    # detail indicates  whether we can do this on the list (false), or only a single item (true)
    @action(methods=['get'], detail=True, url_path='image', name='image')
    def image(self, request, **kwargs):
        author_id = kwargs['author_pk']
        post_id = kwargs['pk']

        img = get_object_or_404(Post.objects, author_id=author_id, pk=post_id)

        if img.content_type != ContentType.PNG and img.content_type != ContentType.JPG:
            return Response(status=404)

        with open(os.path.abspath(settings.BASE_DIR) + img.img_content.url, 'rb') as img_file:
            encoded_img = base64.b64encode(img_file.read()).decode('utf-8')

        return HttpResponse(f'data:{img.content_type},{encoded_img}', content_type=img.content_type)
