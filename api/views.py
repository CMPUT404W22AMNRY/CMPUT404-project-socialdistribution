from json import JSONDecodeError, loads as json_loads
from typing import Any
from follow.models import Follow
from posts.models import Post, ContentType, Like
from api.util import page_number_pagination_class_factory
from rest_framework.views import APIView
from rest_framework.exceptions import MethodNotAllowed
from api.serializers import AuthorSerializer, CommentSerializer, FollowersSerializer, PostSerializer, LikesSerializer
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse
from django.http.request import HttpRequest
from rest_framework.request import Request
import requests
from django.http import HttpResponse
import base64
from urllib.parse import urlparse


class AuthorViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'authors')])

    queryset = get_user_model().objects.filter(is_active=True, is_staff=False, is_api_user=False).order_by('id')
    serializer_class = AuthorSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']  # Allow 'post', 'delete' on actions but don't allow POST to create

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed('DELETE')

    @action(methods=['post', 'get', 'delete'], detail=True, url_path='inbox', name='inbox')
    def inbox(self, request: HttpRequest, **kwargs):
        author_id = kwargs['pk']
        http_method_name = request.method.lower()
        if http_method_name == 'post':
            try:
                body: dict[str, Any] = json_loads(request.body)
            except JSONDecodeError as err:
                return HttpResponse(err, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            post_type = body.get('type').lower()

            if post_type == 'post':
                # TODO: Handle post
                return HttpResponse({}, status=status.HTTP_501_NOT_IMPLEMENTED)

            if post_type == 'follow':
                # TODO: Handle follow request
                return HttpResponse({}, status=status.HTTP_501_NOT_IMPLEMENTED)

            if post_type == 'like':
                return handle_inbox_like(request, body)

            if post_type == 'comment':
                # TODO: Handle comment
                return HttpResponse({}, status=status.HTTP_501_NOT_IMPLEMENTED)

            return HttpResponse({'detail': 'Unknown type'},
                                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                content_type='applicaton/json')

        if http_method_name == 'get':
            # TODO: Implement
            return HttpResponse({}, status=status.HTTP_501_NOT_IMPLEMENTED)

        if http_method_name == 'delete':
            # TODO: Implement
            return HttpResponse({}, status=status.HTTP_501_NOT_IMPLEMENTED)

        raise MethodNotAllowed(request.method)


class PostViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'posts')])

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        return Post.objects.filter(author=self.kwargs['author_pk']).order_by('-date_published')

    # detail indicates  whether we can do this on the list (false), or only a single item (true)
    @action(methods=['get'], detail=True, url_path='image', name='image')
    def image(self, request, **kwargs):
        author_id = kwargs['author_pk']
        post_id = kwargs['pk']

        post = get_object_or_404(Post.objects, author_id=author_id, pk=post_id)

        if post.content_type != ContentType.PNG and post.content_type != ContentType.JPG:
            return Response(status=404)

        location = post.img_content.url if post.img_content else post.content
        encoded_img = base64.b64encode(requests.get(location).content)

        return HttpResponse(encoded_img, content_type=post.content_type)


class FollowersViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'followers')])
    serializer_class = FollowersSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'put', 'delete']

    def get_queryset(self):
        return Follow.objects.filter(followee=self.kwargs['author_pk']).order_by('-created')

    def update(self, request, *args, **kwargs):
        followee_id = kwargs['author_pk']
        follower_id = kwargs['pk']
        try:
            followee = get_user_model().objects.get(id=followee_id)
            follower = get_user_model().objects.get(id=follower_id)
        except get_user_model().DoesNotExist as e:
            raise Http404

        follow, create = Follow.objects.get_or_create(followee=followee, follower=follower)
        if not create:
            return Response(status.HTTP_204_NO_CONTENT)
        else:
            return Response(status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        followee_id = kwargs['author_pk']
        follower_id = kwargs['pk']
        try:
            followee = get_user_model().objects.get(id=followee_id)
            follower = get_user_model().objects.get(id=follower_id)
        except get_user_model().DoesNotExist as e:
            raise Http404
        Follow.objects.unfollow(followee=followee, follower=follower)
        return Response(status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        followee_id = kwargs['author_pk']
        follower_id = kwargs['pk']
        try:
            followee = get_user_model().objects.get(id=followee_id)
            follower = get_user_model().objects.get(id=follower_id)
        except get_user_model().DoesNotExist as e:
            raise Http404

        follow = get_object_or_404(Follow.objects, follower=follower, followee=followee)
        serializer = self.serializer_class(follow, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class LikesViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'likes')])

    serializer_class = LikesSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        return Post.objects.get(pk=self.kwargs['post_pk']).like_set.all().order_by('author_id')


class LikedViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'liked')])

    serializer_class = LikesSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        return Like.objects.filter(author_id=self.kwargs['author_pk'])


class CommentViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'comments')], items_field_name='comments')

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        return Post.objects.get(pk=self.kwargs['post_pk']).comment_set.all().order_by('-date_published')


class InboxView(APIView):
    def post(self, request: Request, format=None):
        # TODO: Implement this
        return Response({}, status=status.HTTP_501_NOT_IMPLEMENTED)

def handle_inbox_like(request: Request, body: dict[str, Any]) -> Response:
    requesting_author_id: str = body.get('author').get('id')
    post_or_comment_id: str = body.get('object')

    parsed_post_or_comment_id = urlparse(post_or_comment_id)
    parsed_author_id = urlparse(requesting_author_id)
    if not parsed_author_id.hostname == request.get_host():
        # Remote likes
        return HttpResponse({}, status=status.HTTP_501_NOT_IMPLEMENTED)

    # Get last path of url
    # https://stackoverflow.com/questions/7253803/how-to-get-everything-after-last-slash-in-a-url
    requesting_author_id = parsed_author_id.path.rsplit('/', 1)[-1]

    if '/comment/' in post_or_comment_id:
        # Comment like
        return HttpResponse({}, status=status.HTTP_501_NOT_IMPLEMENTED)

    post_id = parsed_post_or_comment_id.path.rsplit('/', 1)[-1]

    like = Like.objects.create(
        author_id=requesting_author_id,
        post_id=post_id,
    )
    like.save()

    serialized = LikesSerializer(like, context={'request': request}).data
    return Response(serialized)
