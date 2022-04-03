from urllib.parse import urlparse
import base64
from django.http import HttpResponse
import requests
from rest_framework.request import Request
from django.http.request import HttpRequest
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from api.serializers import AuthorSerializer, CommentSerializer, FollowersSerializer, PostSerializer, LikesSerializer, RemoteLikeSerializer
from api.serializers import AuthorSerializer, CommentSerializer, FollowersSerializer, PostSerializer, LikesSerializer, CommentLikeSerializer
from rest_framework.exceptions import MethodNotAllowed
from api.util import page_number_pagination_class_factory
from posts.models import Post, ContentType, Like, RemoteLike
from posts.models import Post, ContentType, Like, Comment
from json import JSONDecodeError, loads as json_loads
from typing import Any
from follow.models import Follow


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
    http_method_names = ['get', 'post', 'delete', 'put']

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

    def create(self, request: Request, *args, **kwargs):
        if request.user.is_api_user:
            raise PermissionDenied(detail='No access to local objects', code=status.HTTP_403_FORBIDDEN)
        if request.user.id != int(kwargs['author_pk']):
            raise PermissionDenied(
                detail='Cannot create post on behalf of another user',
                code=status.HTTP_403_FORBIDDEN)
        # https://stackoverflow.com/questions/44717442/this-querydict-instance-is-immutable
        request.data._mutable = True
        request.data['author_id'] = kwargs['author_pk']
        request.data._mutable = False
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_api_user:
            raise PermissionDenied(detail='No access to local objects', code=status.HTTP_403_FORBIDDEN)
        if request.user.id != int(kwargs['author_pk']):
            raise PermissionDenied(
                detail='Cannot delete post on behalf of another user',
                code=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user.is_api_user:
            raise PermissionDenied(detail='No access to local objects', code=status.HTTP_403_FORBIDDEN)
        if request.user.id != int(kwargs['author_pk']):
            raise PermissionDenied(
                detail='Cannot update post on behalf of another user',
                code=status.HTTP_403_FORBIDDEN)
        request.data['author_id'] = kwargs['author_pk']
        return super().update(request, *args, **kwargs)


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

    def list(self, request, *args, **kwargs):
        response: Response = super().list(request, *args, **kwargs)

        remote_like_query_set = Post.objects.get(pk=self.kwargs['post_pk']).remotelike_set.all().order_by('author_url')
        serialized_remote_likes = RemoteLikeSerializer(remote_like_query_set, many=True, context={'request': request})

        if len(serialized_remote_likes.data) > 0:
            response.data['items'] += (serialized_remote_likes.data)
        return response


class LikedViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'liked')])

    serializer_class = LikesSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        return Like.objects.filter(author_id=self.kwargs['author_pk']).order_by('author_id')


class CommentViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'comments')], items_field_name='comments')

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        return Post.objects.get(pk=self.kwargs['post_pk']).comment_set.all().order_by('-date_published')


class CommentLikesViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    pagination_class = page_number_pagination_class_factory([('type', 'likes')])

    serializer_class = CommentLikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        return Comment.objects.get(pk=self.kwargs['comment_pk']).commentlike_set.all().order_by('author_id')


def handle_inbox_like(request: Request, body: dict[str, Any]) -> Response:
    author_id: str = body.get('author').get('id')
    post_or_comment_id: str = body.get('object')

    parsed_post_or_comment_id = urlparse(post_or_comment_id)
    parsed_author_id = urlparse(author_id)

    if '/comment/' in post_or_comment_id:
        # Comment like
        return HttpResponse({}, status=status.HTTP_501_NOT_IMPLEMENTED)

    post_id = parsed_post_or_comment_id.path.rsplit('/', 1)[-1]

    if not parsed_author_id.hostname == request.get_host():
        # Remote likes
        remote_like = RemoteLike.objects.create(author_url=author_id, post_id=post_id)
        remote_like.save()

        return HttpResponse({}, status=status.HTTP_204_NO_CONTENT)

    # Get last path of url
    # https://stackoverflow.com/questions/7253803/how-to-get-everything-after-last-slash-in-a-url
    local_author_id = parsed_author_id.path.rsplit('/', 1)[-1]

    like = Like.objects.create(
        author_id=local_author_id,
        post_id=post_id,
    )
    like.save()

    serialized = LikesSerializer(like, context={'request': request}).data
    return Response(serialized)
