from django.urls import reverse
from requests import Response
from urllib.parse import urlparse
from servers.models import Server
from follow.models import Follow, Request, RemoteFollower, RemoteRequest
from posts.models import Post, Like, Comment, RemoteComment, RemoteLike
from posts.models import CommentLike, Post, Like, Comment
import json
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['url', ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = 'author'
        representation['displayName'] = instance.get_full_name()
        representation['github'] = instance.github_url
        representation['profileImage'] = instance.profile_image_url
        representation['id'] = representation['url']
        return representation


class CommentSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'author_pk': 'author__pk',
        'post_pk': 'post__pk',
    }
    author = AuthorSerializer(many=False, read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'comment', 'url']

    def to_representation(self, instance: Comment):
        representation = super().to_representation(instance)
        representation['type'] = 'comment'
        representation['contentType'] = instance.content_type
        representation['published'] = instance.date_published
        representation['id'] = representation['url']
        del representation['url']
        return representation


class PostSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'author_pk': 'author__pk',
    }
    author = AuthorSerializer(many=False, read_only=True)
    comment_set = CommentSerializer(many=True, read_only=True)
    url_field_name = 'source'

    class Meta:
        model = Post
        fields = ['title', 'description', 'content', 'author', 'visibility', 'unlisted', 'source', 'comment_set']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = 'post'
        representation['contentType'] = instance.content_type
        representation['published'] = instance.date_published
        representation['categories'] = [category.category for category in instance.categories.all()]
        representation['origin'] = representation['source']  # TODO: Update this when we have post sharing
        representation['count'] = len(instance.comment_set.all())
        representation['commentsSrc'] = {
            'type': 'comments',
            'page': 1,
            'post': representation['source'],
            'id': representation['source'] + '/comments',
            'comments': representation['comment_set']
        }
        del representation['comment_set']
        representation['id'] = representation['source']
        return representation

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        internal_value['author_id'] = data['author_id']
        return internal_value


class FollowersSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'author_pk': 'author__pk',
    }
    follower = AuthorSerializer(many=False, read_only=True)

    class Meta:
        model = Follow
        fields = ['follower']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation['follower']


class RequestSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'author_pk': 'author__pk'
    }
    from_user = AuthorSerializer(many=False, read_only=True)
    to_user = AuthorSerializer(many=False, read_only=True)

    class Meta:
        model = Request
        fields = ['from_user', 'to_user']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = 'Follow'
        representation['summary'] = instance.from_user.get_full_name() + " wants to follow " + \
            instance.to_user.get_full_name()
        representation['actor'] = representation['from_user']
        del representation['from_user']
        representation['object'] = representation['to_user']
        del representation['to_user']

        return representation


class RemoteRequestSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'author_pk': 'author__pk'
    }
    to_user = AuthorSerializer(many=False, read_only=True)

    class Meta:
        model = RemoteRequest
        fields = ['to_user']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for server in Server.objects.all():
            parsed_from_user_url = urlparse(instance.from_user_url)
            parsed_server_service_address = urlparse(server.service_address)
            if parsed_from_user_url.hostname != parsed_server_service_address.hostname:
                continue
            from_user_response: Response = server.get(parsed_server_service_address.path)
            json_from_user = from_user_response.json()

            from_user_name = json_from_user.get('displayName') or json_from_user.get('display_name') or ''
            representation['type'] = 'Follow'
            representation['summary'] = from_user_name + ' wants to follow ' + instance.to_user.get_full_name()
            representation['actor'] = json_from_user
            representation['object'] = representation['to_user']
            del representation['to_user']
            return representation


class LikesSerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {
        'author_pk': 'author__pk',
        'post_pk': 'post__pk',
    }
    author = AuthorSerializer(many=False, read_only=True)
    post = PostSerializer(many=False, read_only=True)

    class Meta:
        model = Like
        fields = ['author', 'post']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = 'Like'
        representation['summary'] = instance.author.get_full_name() + ' likes your post'
        representation['object'] = representation['post']['source']
        del representation['post']
        return representation


class CommentLikeSerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {
        'author_pk': 'author__pk',
    }
    author = AuthorSerializer(many=False, read_only=True)
    comment = CommentSerializer(many=False, read_only=True)

    class Meta:
        model = CommentLike
        fields = ['author', 'comment']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = 'Like'
        representation['summary'] = instance.author.get_full_name() + ' likes your comment'
        representation['object'] = representation['comment']['id']
        del representation['comment']
        return representation


class RemoteLikeSerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {
        'post_pk': 'post__pk',
    }
    post = PostSerializer(many=False, read_only=True)

    class Meta:
        model = RemoteLike
        fields = ['post']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for server in Server.objects.all():
            parsed_author_url = urlparse(instance.author_url)
            parsed_server_service_address = urlparse(server.service_address)
            if parsed_author_url.hostname != parsed_server_service_address.hostname:
                continue
            author: Response = server.get(parsed_author_url.path)
            json_author = author.json()

            author_name = json_author.get('displayName') or json_author.get('display_name') or ''
            representation['type'] = 'Like'
            representation['summary'] = author_name + ' likes your post'
            representation['object'] = representation['post']['source']
            representation['author'] = json_author
            del representation['post']
            return representation
        return representation


class RemoteCommentSerializer(NestedHyperlinkedModelSerializer):
    class Meta:
        model = RemoteComment
        fields = ['comment']

    def to_representation(self, instance: RemoteComment):
        representation = super().to_representation(instance)
        for server in Server.objects.all():
            parsed_author_url = urlparse(instance.author_url)
            parsed_server_service_address = urlparse(server.service_address)
            if parsed_author_url.hostname != parsed_server_service_address.hostname:
                continue
            author: Response = server.get(parsed_author_url.path)
            json_author = author.json()

            representation['type'] = 'comment'
            representation['contentType'] = instance.content_type
            representation['published'] = instance.date_published
            representation['author'] = json_author
            # TODO: Get comment id (absolute url in service)
            return representation
        return representation
