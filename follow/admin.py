from django.contrib import admin
from django.urls import reverse
from django.contrib.auth import get_user_model

import auth_provider.user_action_generators as user_action_generators
from .models import Follow, Request

USER_MODEL = get_user_model()


class FollowAdmin(admin.ModelAdmin):
    model = Follow
    raw_id_feild = ("follwer", "followee")


class RequestAdmin(admin.ModelAdmin):
    model = Request
    raw_id_feild = ("from_user", "to_user")


admin.site.register(Follow, FollowAdmin)
admin.site.register(Request, RequestAdmin)


def AddFriendAction(current_user: USER_MODEL, target_user: USER_MODEL) -> str:
    if Follow.objects.check_follow(follower=current_user, followee=target_user):
        return ('', '')
    try:
        Request.objects.get(
            from_user=current_user,
            to_user=target_user)
    except Request.DoesNotExist:
        return ('Add friend', reverse('follow:create_follow_request', kwargs={'to_username': target_user.username}))
    return ('', '')


user_action_generators.register(AddFriendAction)
