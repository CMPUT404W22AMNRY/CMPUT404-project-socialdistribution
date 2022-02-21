from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse


def root(request: HttpRequest) -> HttpResponse:
    if request.user.is_anonymous:
        return redirect(reverse_lazy('auth_provider:login'))
    # TODO: redirect to user's stream page
    return HttpResponse("Main app")
