from typing import Any
from django.urls import reverse_lazy, reverse
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from requests import Response
import urllib.parse

from posts.models import Post
from servers.views.generic.list_view import ServerListView
from servers.models import Server
from follow.models import Follow


def root(request: HttpRequest) -> HttpResponse:
    if request.user.is_anonymous:
        return redirect(reverse_lazy('auth_provider:login'))
    return redirect(reverse('stream'))


class StreamView(LoginRequiredMixin, ServerListView):
    model = Post
    paginate_by = 10
    template_name = 'stream.html'

    def get_queryset(self) -> QuerySet[Post]:
        public_posts = Post.objects.filter(visibility=Post.Visibility.PUBLIC, unlisted=False)
        query_set = public_posts
        for friend in Follow.objects.followers(self.request.user):
            query_set = query_set.union(friend.post_set.filter(visibility=Post.Visibility.FRIENDS, unlisted=False))
        return query_set

    def get_server_to_endpoints_mapping(self) -> list[tuple[Server, list[str]]]:
        server_endpoints_tuples = []
        for server in Server.objects.all():
            resp = server.get('/authors')
            authors_endpoint = server.service_address + '/authors/'
            authors = resp.json()['items']
            endpoints = []
            for author in authors:
                # TODO: Update this to author_url once our groupmates are ready (have the URL field)
                author_id = author['id']
                if isinstance(author_id, str) and author_id.startswith(authors_endpoint):
                    author_id = author_id[len(authors_endpoint):]
                authors_posts = f'/authors/{author_id}/posts'
                endpoints.append(authors_posts)
            server_endpoints_tuples.append((server, endpoints))
        return server_endpoints_tuples

    def serialize(self, response: Response) -> list:
        json_response = response.json()

        def to_internal(representation: dict[str, Any]):
            request_url = response.url
            if not request_url.endswith('/'):
                request_url += '/'
            # TODO: Update this to source or origin
            post_url = urllib.parse.urljoin(request_url, str(representation['id']))
            absolute_url = reverse('posts:remote-detail', kwargs={'url': post_url})
            return {
                'title': representation.get('title'),
                'description': representation.get('description'),
                'content_type': representation.get('contentType') or representation.get('content_type'),
                'content': representation.get('content'),
                'date_published': representation.get('published'),
                'get_absolute_url': absolute_url,
                'author': {
                    'get_full_name': '' if isinstance(
                        representation.get('author'),
                        str) else representation.get('author').get('displayName') or representation.get('author').get('display_name')}}

        # TODO: Remove this if group 13 implements placing posts under items
        if isinstance(json_response, list):
            return [to_internal(post) for post in json_response]

        return [to_internal(post) for post in json_response['items']]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['object_list'] = sorted(context['object_list'], key=lambda x: str(x.date_published) if isinstance(x, Post) else x['date_published'], reverse=True)
        return context
