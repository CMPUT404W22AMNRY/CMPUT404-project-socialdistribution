import json
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from posts.models import Post, Like, Comment, RemoteLike
from follow.models import Follow
from servers.models import Server
from urllib.parse import urlparse
from requests import Response


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
            author: Response = server.get(parsed_server_service_address.path)
            json_author = author.json()

            author_name = json_author.get('displayName') or json_author.get('display_name') or ''
            representation['type'] = 'Like'
            representation['summary'] = author_name + ' likes your post'
            representation['object'] = representation['post']['source']
            representation['author'] = json_author
            del representation['post']
            return representation
        return representation
