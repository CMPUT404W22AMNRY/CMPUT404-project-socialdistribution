from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.generic.list import ListView
from follow.models import AlreadyExistsError, Follow, Request
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db.models import Q


USER_MODEL = get_user_model()


def get_follow_list():
    return getattr(settings, "FOLLOW_LIST", "users")


def create_follow_request(request, to_username):
    payload = {"to_username": to_username}
    if request.method == 'POST':
        to_user = USER_MODEL.objects.get(username=to_username)
        from_user = request.user
        try:
            Follow.objects.follow_request(from_user, to_user)
        except AlreadyExistsError as e1:
            payload["error"] = str(e1)
        except ValidationError as e2:
            payload["error"] = str(e2)
        else:
            return redirect("/")  # TODO need to be update

    return render(request, template_name='./create_follow_request.html', context=payload)


def accept_follow_request(request, from_username):
    payload = {"from_username": from_username}
    if request.method == 'POST':
        from_user = USER_MODEL.objects.get(username=from_username)
        to_user = request.user
        try:
            request_accept = Request.objects.get(from_user=from_user, to_user=to_user)
            request_accept.accept()
            request_accept.save()
        except AlreadyExistsError as e1:
            payload["error"] = str(e1)
        except ValidationError as e2:
            payload["error"] = str(e2)
        else:
            return redirect("/")  # TODO need to be update
    return render(request, template_name='./accept_follow_request.html', context=payload)


def reject_follow_request(request, from_username):
    payload = {"from_username": from_username}
    if request.method == 'POST':
        from_user = USER_MODEL.objects.get(username=from_username)
        to_user = request.user
        try:
            request_accept = Request.objects.get(from_user=from_user, to_user=to_user)
            request_accept.reject()
        except ValidationError as e2:
            payload["error"] = str(e2)
        else:
            return redirect("/")  # TODO need to be update
    return render(request, template_name='./reject_follow_request.html', context=payload)


def unfollow_request(request, from_username):
    payload = {"from_username": from_username}
    if request.method == 'POST':
        from_user = USER_MODEL.objects.get(username=from_username)
        to_user = request.user
        try:
            Follow.objects.unfollow(from_user, to_user)
        except AlreadyExistsError as e1:
            payload["error"] = str(e1)
        except ValidationError as e2:
            payload["error"] = str(e2)
        else:
            return redirect("/")  # TODO need to be update
    return render(request, template_name='./unfollow_request.html', context=payload)


def remove_follow_request(request, to_username):
    payload = {"to_username": to_username}
    if request.method == 'POST':
        to_user = USER_MODEL.objects.get(username=to_username)
        from_user = request.user
        try:
            Follow.objects.unfollow(from_user, to_user)
        except AlreadyExistsError as e1:
            payload["error"] = str(e1)
        except ValidationError as e2:
            payload["error"] = str(e2)
        else:
            return redirect("/")  # TODO need to be update
    return render(request, template_name='./remove_follow_request.html', context=payload)


class UsersView(LoginRequiredMixin, ListView):
    model = USER_MODEL
    paginate_by = 100
    template_name = 'follow/user_list.html'

    def get_queryset(self):
        return USER_MODEL.objects.filter(~Q(pk=self.request.user.id) & Q(is_staff=False))


class FriendRequestsView(LoginRequiredMixin, ListView):
    model = Request
    paginate_by = 100
    template_name = 'follow/request_list.html'

    def get_queryset(self):
        return Request.objects.request(user=self.request.user)
