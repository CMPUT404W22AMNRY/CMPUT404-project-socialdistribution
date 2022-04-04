from typing import Any
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.list import ListView
from follow.models import AlreadyExistsError, Follow, RemoteFollower, Request, RemoteRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db.models import Q
from requests import Response

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


def accept_remote_follow_request(request, from_user_url):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        remote_request = RemoteRequest.objects.get(to_user=request.user, from_user_url=from_user_url)
        remote_request.accept()
    except AlreadyExistsError:
        pass
    finally:
        return redirect(reverse('auth_provider:remote_profile', kwargs={'url': from_user_url}))


def reject_remote_follow_request(request, from_user_url):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        remote_request = RemoteRequest.objects.get(to_user=request.user, from_user_url=from_user_url)
        remote_request.reject()
    except RemoteRequest.DoesNotExist:
        pass
    finally:
        return redirect(reverse('auth_provider:remote_profile', kwargs={'url': from_user_url}))


def remove_remote_follower(request, from_user_url):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        follow = RemoteFollower.objects.get(followee=request.user, follower_url=from_user_url)
        follow.unfollow()
    except AlreadyExistsError as e1:
        pass
    except ValidationError as e2:
        pass
    finally:
        return redirect(reverse('auth_provider:remote_profile', kwargs={'url': from_user_url}))


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
    context_object_name = 'requests'
    template_name = 'follow/request_list.html'

    def get_queryset(self):
        return Request.objects.filter(to_user=self.request.user)

    def get_context_data(self, **kwargs: Any):
        context = super(FriendRequestsView, self).get_context_data(**kwargs)
        context['remote_requests'] = RemoteRequest.objects.filter(to_user=self.request.user)
        return context


class MyFriendsView(LoginRequiredMixin, ListView):
    model = USER_MODEL
    template_name = 'follow/friend_list.html'

    def get_queryset(self):
        return Follow.objects.true_friend(self.request.user)
