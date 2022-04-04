import json
from typing import Optional
from django.contrib import admin
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from requests import Response
from auth_provider import remote_action_generators, user_resources
from urllib.parse import urlparse

import auth_provider.user_action_generators as user_action_generators
from .models import Follow, Request, RemoteFollow
from servers.models import Server

USER_MODEL = get_user_model()


class FollowAdmin(admin.ModelAdmin):
    model = Follow
    raw_id_feild = ("follwer", "followee")


class RequestAdmin(admin.ModelAdmin):
    model = Request
    raw_id_feild = ("from_user", "to_user")


admin.site.register(Follow, FollowAdmin)
admin.site.register(Request, RequestAdmin)


# Register add friend function to user profile page
def AddFriendAction(current_user: USER_MODEL, target_user: USER_MODEL) -> Optional[tuple[str, str]]:
    if Follow.objects.check_follow(follower=current_user, followee=target_user):
        return None
    try:
        Request.objects.get(
            from_user=current_user,
            to_user=target_user)
    except Request.DoesNotExist:
        return ('Add friend', reverse('follow:create_follow_request', kwargs={'to_username': target_user.username}))
    return None


user_action_generators.register(AddFriendAction)


def UnfollowAction(current_user: USER_MODEL, target_user: USER_MODEL) -> Optional[tuple[str, str]]:
    if not Follow.objects.check_follow(follower=current_user, followee=target_user):
        return None
    return ('Unfollow', reverse('follow:unfollow_request', kwargs={'from_username': target_user.username}))


user_action_generators.register(UnfollowAction)


def RemoteFriendAction(current_user: USER_MODEL, target_url: str) -> Optional[tuple[str, str]]:

    return ('Add friend', reverse('follow:remote_request', kwargs={'url': target_url}))

def RemoteUnfollowAction(current_user: USER_MODEL, target_url: str) -> Optional[tuple[str, str]]:

    return ('Unfollow', reverse('follow:remote_unfollow', kwargs={'url': target_url}))


remote_action_generators.register(RemoteFriendAction)


remote_action_generators.register(RemoteUnfollowAction)


# Register Friends page to my profile page
user_resources.register(resource_name='Friends', link_to_user_resource=reverse_lazy('follow:friends'))
