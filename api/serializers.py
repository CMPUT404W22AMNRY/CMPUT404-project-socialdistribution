from django.contrib.auth import get_user_model
from rest_framework.serializers import HyperlinkedModelSerializer, HyperlinkedIdentityField
from rest_framework_nested.relations import NestedHyperlinkedRelatedField
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from posts.models import Post


class AuthorSerializer(HyperlinkedModelSerializer):        
    
    class Meta:
        model = get_user_model()
        fields = ['id', 'url', ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = 'author'
        representation['displayName'] = instance.get_full_name()
        representation['github'] = instance.github_url
        representation['profileImage'] = instance.profile_image_url
        return representation

class PostSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'author_pk': 'author__pk',
    }    

    # TODO: Create post serializer 
    class Meta:
        model = Post
        fields = ['id', ] # TODO: hyperlinking is broken atm... :( will fix eventually - Reilly

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = 'post'
        representation['title'] = instance.title
        representation['description'] = instance.description
        representation['contentType'] = instance.content_type
        representation['content'] = instance.content
        return representation
