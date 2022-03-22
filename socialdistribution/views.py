from django.urls import reverse_lazy, reverse
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from django.db.models import QuerySet

from posts.models import Post


def root(request: HttpRequest) -> HttpResponse:
    if request.user.is_anonymous:
        return redirect(reverse_lazy('auth_provider:login'))
    return redirect(reverse('stream'))


class StreamView(LoginRequiredMixin, ListView):
    model = Post
    paginate_by = 10
    template_name = 'stream.html'

    def get_queryset(self) -> QuerySet[Post]:
        return Post.objects.filter(
            visibility=Post.Visibility.PUBLIC,
            unlisted=False).order_by('-date_published')
