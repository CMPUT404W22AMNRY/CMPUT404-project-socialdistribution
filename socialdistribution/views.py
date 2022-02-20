from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render


def root(request: HttpRequest) -> HttpResponse:
    if request.user.is_anonymous:
        return redirect('login')
    return stream(request)


def stream(request: HttpRequest) -> HttpResponse:
    return render(request, 'stream.html')
