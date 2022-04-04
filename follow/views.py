import json
from typing import Any
from urllib.parse import urlparse
from django.core.exceptions import ValidationError
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.list import ListView
from follow.models import AlreadyExistsError, Follow, RemoteFollow, Request
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db.models import Q
from requests import Response
from servers.models import Server

from lib.url import get_github_user_from_url
from servers.views.generic.list_view import ServerListView


USER_MODEL = get_user_model()


def create_follow_request(request, to_username):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    to_user = USER_MODEL.objects.get(username=to_username)
    from_user = request.user
    try:
        Follow.objects.follow_request(from_user, to_user)
    except AlreadyExistsError as e1:
        pass
    except ValidationError as e2:
        pass
    finally:
        return redirect(to_user.get_absolute_url())


def accept_follow_request(request, from_username):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    from_user = USER_MODEL.objects.get(username=from_username)
    to_user = request.user
    try:
        request_accept = Request.objects.get(from_user=from_user, to_user=to_user)
        request_accept.accept()
        request_accept.save()
    except AlreadyExistsError:
        pass
    finally:
        return redirect(from_user.get_absolute_url())


def reject_follow_request(request, from_username):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    from_user = USER_MODEL.objects.get(username=from_username)
    to_user = request.user
    try:
        request_accept = Request.objects.get(from_user=from_user, to_user=to_user)
        request_accept.reject()
    except ValidationError as e2:
        pass
    finally:
        return redirect(from_user.get_absolute_url())


def unfollow_request(request, from_username):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    from_user = USER_MODEL.objects.get(username=from_username)
    try:
        Follow.objects.unfollow(follower=request.user, followee=from_user)
    except AlreadyExistsError as e1:
        pass
    except ValidationError as e2:
        pass
    finally:
        return redirect(from_user.get_absolute_url())

def remote_friend_request(request, target_url):
    def serialize(actor, object):
        object_dict = json.loads(object)
        object_name = object.get('displayName') or object.get('display_name') or ''
        acotr_host = urlparse(actor.get_absolute_url()).hostname
        return {
            'type': 'Follow',
            'summary': actor.get_full_name + ' wants to follow ' + object_name,
            'actor': {
                "type": 'author',
                "id": actor.id,
                "url": actor.get_absolute_url(),
                "host": 'http://' + acotr_host,
                "displayName": actor.get_full_name(),
                "github": actor.github_url,
                "profileImage": actor.profile_image_url
            },
            'object': object_dict
        }

    remote_follow = RemoteFollow.objects.create(from_user=request.user, to_user_url=target_url)
    remote_follow.save()
    for server in Server.objects.all():
        parsed_target_url = urlparse(target_url)
        parsed_server_address = urlparse(server.service_address)
        if parsed_target_url.hostname != parsed_server_address:
            continue
        follow_object: Response = server.get(parsed_target_url.path)
        data = serialize(request.user, follow_object.json())
        server.post(parsed_target_url.path + '/inbox/', data)
        break
    return redirect(reverse('auth_provider:remote_profile', kwargs={'url': target_url}))

def remote_unfollow(request, target_url):
    try:
        remote_follow = RemoteFollow.objects.get(from_user=request.user, to_user_url=target_url)
        for server in Server.objects.all():
            parsed_target_url = urlparse(target_url)
            parsed_server_address = urlparse(server.service_address)
            if parsed_target_url.hostname != parsed_server_address:
                continue
            server.delete(parsed_target_url.path + '/followers/' + request.user.id + '/')
            remote_follow.delete()
            break
    except RemoteFollow.DoesNotExist:
        pass
    return redirect(reverse('auth_provider:remote_profile', kwargs={'url': target_url}))


class UsersView(LoginRequiredMixin, ServerListView):
    model = USER_MODEL
    template_name = 'follow/user_list.html'
    endpoint = '/authors'

    def serialize(self, response: Response):
        jsonResponse = response.json()

        def to_internal(representation: dict[str, Any]):
            return {
                'get_full_name': representation.get('displayName') or representation.get('display_name'),
                'profile_image_url': representation.get('profileImage'),
                'username': get_github_user_from_url(representation.get('github')) or representation.get('github'),
                'get_absolute_url': reverse(
                    'auth_provider:remote_profile',
                    kwargs={
                        'url': representation.get('id')
                    }
                )
            }

        return [to_internal(user) for user in jsonResponse['items']]

    def get_queryset(self):
        return USER_MODEL.objects.filter(~Q(pk=self.request.user.id) & Q(is_staff=False) & Q(is_api_user=False))


class FriendRequestsView(LoginRequiredMixin, ListView):
    model = Request
    template_name = 'follow/request_list.html'

    def get_queryset(self):
        return Request.objects.filter(to_user=self.request.user)


class MyFriendsView(LoginRequiredMixin, ListView):
    model = USER_MODEL
    template_name = 'follow/friend_list.html'

    def get_queryset(self):
        return Follow.objects.true_friend(self.request.user)
