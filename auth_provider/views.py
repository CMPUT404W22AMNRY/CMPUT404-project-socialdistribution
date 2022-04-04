from urllib.parse import urlparse
import requests
import json
from typing import Any, Dict, Optional
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth import get_user_model, logout
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView
from requests import Response
from follow.models import RemoteFollow
from servers.models import Server

from servers.views.generic.detailed_view import ServerDetailView

from lib.constants import GitHub_EventType
from lib.url import get_github_user_from_url
from .user_resources import user_resources
from .forms import SignUpForm, EditProfileForm
from .user_action_generators import UserActionGenerator, user_action_generators
from .remote_action_generators import RemoteActionGenerator, remote_action_generators


class SignUpView(CreateView):
    template_name = 'auth/signup.html'
    form_class = SignUpForm
    success_url = reverse_lazy('auth_provider:login')


class MyProfileView(DetailView):
    model = get_user_model()
    template_name = 'profile/my_profile.html'

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context['github_activity'] = get_github_activity(self.object.github_url)
        context['user_resources'] = [{'name': user_resource[0], 'link': user_resource[1]}
                                     for user_resource in user_resources]
        return context


class ProfileView(DetailView):
    model = get_user_model()
    template_name = 'profile/user_profile.html'

    def get_context_object_name(self, obj: Any) -> Optional[str]:
        return 'object'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        def get_action(user_action_generator: UserActionGenerator):
            user_action = user_action_generator(self.request.user, self.get_object())
            if user_action is None:
                return None
            return {
                'name': user_action[0],
                'link': user_action[1],
            }

        context['github_activity'] = get_github_activity(self.object.github_url)
        # TODO: Clean this up with a lambda
        actions = [get_action(user_action_generator)
                   for user_action_generator in user_action_generators]
        context['user_actions'] = []
        for action in actions:
            if action is not None:
                context['user_actions'].append(action)

        return context


class RemoteProfileView(ServerDetailView):
    model = get_user_model()
    template_name = 'profile/remote_user_profile.html'

    def get_context_object_name(self, obj: Any) -> Optional[str]:
        return 'object'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        def remote_action(remote_action_generator: RemoteActionGenerator):
            print(self.get_object()['id'])
            remote_action = remote_action_generator(self.request.user, self.get_object()['id'])
            if remote_action is None:
                return None
            return {
                'name': remote_action[0],
                'link': remote_action[1]
            }

        # TODO: Get user actions for remote users
        context['github_activity'] = get_github_activity(self.object['github_url'])
        context['user_actions'] = []
        actions = [remote_action(remote_action_generator)
                   for remote_action_generator in remote_action_generators]
        try:
            remote_follow = RemoteFollow.objects.get(from_user=self.request.user, to_user_url=self.get_object()['id'])
            for server in Server.objects.all():
                parsed_target_url = urlparse(self.get_object().id)
                parsed_server_address = urlparse(server.service_address)
                if parsed_target_url.hostname != parsed_server_address:
                    continue
                follower: Response = server.get(parsed_target_url.path + '/followers/')
                json_follower = follower.json()
                if self.request.user.id in json_follower['items'].__str__():
                    remote_follow.approved = True
                    context['user_actions'] = actions[1]
                break
        except RemoteFollow.DoesNotExist:
            context['user_actions'] = actions[0]

        return context

    def to_internal(self, response: Response) -> get_user_model():
        json_response = response.json()

        profile_image_url = json_response.get('profileImage') or json_response.get('profile_image')
        author_full_name = json_response.get('displayName') or json_response.get('display_name')
        github = json_response.get('github')

        return {
            'profile_image_url': profile_image_url,
            "get_full_name": author_full_name,
            "github_url": github
        }


class EditProfileView(UpdateView):
    form_class = EditProfileForm
    model = get_user_model()
    template_name = 'profile/edit_profile.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self) -> str:
        return reverse('auth_provider:my_profile')


def logout_view(request):
    logout(request)
    return redirect('/')


def get_github_activity(github_url: str):
    github_username = get_github_user_from_url(github_url)
    if not github_username:
        return None

    def send_get_github_activity(user: str, page: int = 1):
        return requests.get(
            f'https://api.github.com/users/{user}/events?accept=application/vnd.github.v3+json&per_page=100&page={page}')

    page = 1
    activity = {
        'username': github_username,
        'commits': 0,
        'pull_requests': 0,
        'reviews': 0,
        'issues': 0,
    }
    success = False
    while True:
        github_activity_request = send_get_github_activity(github_username, page)
        if github_activity_request.status_code == 200:
            parse_github_activity(activity, github_activity_request.json())
            success |= True
        else:
            print('GitHub activity request failed with code ' + github_activity_request.status_code)
            break

        if 'Link' in github_activity_request.headers and 'rel="next"' in github_activity_request.headers['Link']:
            page += 1
        else:
            break

    return activity if success else None


def parse_github_activity(activity: dict, json: dict):
    for event in json:
        if event['type'] == GitHub_EventType.PushEvent:
            activity['commits'] += event['payload']['distinct_size']
        if event['type'] == GitHub_EventType.PullRequestEvent and event['payload']['action'] == 'opened':
            activity['pull_requests'] += 1
        if event['type'] == GitHub_EventType.PullRequestReviewEvent:
            activity['reviews'] += 1
        if event['type'] == GitHub_EventType.IssuesEvent:
            activity['issues'] += 1
