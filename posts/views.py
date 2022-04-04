from typing import Any, Dict
from django import forms
from django.db import transaction
from django.forms import ModelForm
from django.http import HttpResponseNotAllowed
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from requests import Response
from lib.http_helper import is_b64_image_content
from django.core.exceptions import PermissionDenied
from urllib.parse import urlparse
from .models import CommentLike, Post, Category, Comment, Like, RemoteComment, RemoteLike
from servers.models import Server
from servers.views.generic.detailed_view import ServerDetailView


class PostForm(ModelForm):
    class Meta:
        model = Post
        exclude = ['author', 'categories']

    categories = forms.CharField(max_length=256)


class CreatePostView(LoginRequiredMixin, CreateView):
    form_class = PostForm
    template_name = 'posts/create_post.html'

    def form_valid(self, form: PostForm) -> HttpResponse:
        form.instance.author = self.request.user

        with transaction.atomic():
            form.save()
            for category in form.cleaned_data['categories'].split(','):
                db_category = Category.objects.get_or_create(category=category.strip())[0]
                form.instance.categories.add(db_category)
            form.save()
        return redirect(form.instance.get_absolute_url())


class EditPostView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/edit_post.html'

    def get_initial(self):
        initial = super().get_initial()
        # Inject categories to text field
        categories = [str(category.category) for category in Post.objects.get(pk=self.kwargs['pk']).categories.all()]
        initial['categories'] = ', '.join(categories)
        return initial

    def form_valid(self, form: PostForm) -> HttpResponse:
        with transaction.atomic():
            form.save()
            for category in form.cleaned_data['categories'].split(','):
                db_category = Category.objects.get_or_create(category=category)[0]
                form.instance.categories.add(db_category)
            form.save()
        return redirect(form.instance.get_absolute_url())

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if self.get_object().author_id != request.user.id:
            raise PermissionDenied("User not allowed to edit another user's post")
        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if self.get_object().author_id != request.user.id:
            raise PermissionDenied("User not allowed to edit another user's post")
        return super().post(request, *args, **kwargs)


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        try:
            Like.objects.get(author=self.request.user, post=self.get_object())
            context['has_liked'] = True
        except Like.DoesNotExist:
            pass
        remote_comments = []
        try:
            remote_comments_queryset = RemoteComment.objects.filter(post=self.get_object())
        except RemoteComment.DoesNotExist:
            pass
        for remote_comment in remote_comments_queryset:
            parsed_author_url = urlparse(remote_comment.author_url)
            author_host = parsed_author_url.hostname
            target_server = None
            for server in Server.objects.all():
                parsed_server_url = urlparse(server.service_address)
                if parsed_server_url.hostname == author_host:
                    target_server = server
                    break

            if target_server is None:
                break

            author_path = remote_comment.author_url[len(target_server.service_address):]
            author_response: Response = target_server.get(author_path)
            author_fullname = author_response.json().get('displayName') or author_response.json().get('display_name')
            remote_comments.append({
                'author': {
                    'get_full_name': author_fullname
                },
                'comment': remote_comment.comment,
                'date_published': remote_comment.date_published,
            })
        context['remote_comments'] = remote_comments
        return context


class RemotePostDetailView(LoginRequiredMixin, ServerDetailView):
    model = Post
    template_name = 'posts/remote_post_detail.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        try:
            # TODO: Fetch likes endpoint
            context['has_liked'] = False
        except Like.DoesNotExist:
            pass
        return context

    def to_internal(self, response: Response) -> Post:
        json_response = response.json()

        content_type = json_response.get('contentType') or json_response.get('content_type')
        is_img = is_b64_image_content(content_type)
        if is_img:
            try:
                origin = json_response.get('origin')
                service_address = origin[0:origin.index('/authors')]
                service_request = origin[origin.index('/authors'):]
                server = Server.objects.get(service_address=service_address)
                img_content = server.get(service_request + '/image').content.decode('utf-8')
            except Exception as e:
                print('warning: ' + e)

        # Build author field
        authors_full_name = ''
        if isinstance(json_response.get('author'), str):
            authors_full_name = json_response.get('author').get(
                'displayName') or json_response.get('author').get('display_name')

        # Build comments field
        def to_comments_internal(json_body: Dict[str, Any]):
            return {
                'comment': json_body.get('comment'),
                'content_type': json_body.get('contentType') or json_body.get('content_type'),
                'date_published': json_body.get('published'),
                'author': {
                    'get_full_name': json_body.get('author').get('displayName') or json_body.get('author').get('display_name')}}

        comments = []
        try:
            comments = [to_comments_internal(comment) for comment in json_response.get('comment_src')]
        except Exception as err:
            pass

        return {
            'id': json_response.get('id'),
            'title': json_response.get('title'),
            'description': json_response.get('description'),
            'content_type': content_type,
            'content': json_response.get('content') if not is_img or not img_content else img_content,
            'categories': json_response.get('categories'),
            'date_published': json_response.get('published'),
            'visibility': json_response.get('visibility'),
            'unlisted': json_response.get('unlisted'),
            'author': {
                'get_full_name': authors_full_name
            },
            'comment_set': {
                'all': comments
            },
        }


class DeletePostView(LoginRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('posts:my-posts')
    template_name = 'posts/delete_post.html'
    template_name_suffix = ''


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        exclude = ['author', 'post']


class CreateCommentView(LoginRequiredMixin, CreateView):
    form_class = CommentForm
    template_name = 'comments/create_comment.html'

    def form_valid(self, form: PostForm) -> HttpResponse:
        post = Post.objects.get(pk=self.kwargs['pk'])
        form.instance.author = self.request.user
        form.instance.post = post
        form.save()
        return redirect(post.get_absolute_url())


class MyPostsView(LoginRequiredMixin, ListView):
    model = Post
    paginate_by = 100
    template_name = 'posts/post_list.html'

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).order_by('-date_published')


def like_post_view(request: HttpRequest, pk: int):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        Like.objects.get(author_id=request.user.id, post_id=pk)
    except Like.DoesNotExist:
        Like.objects.create(author_id=request.user.id, post_id=pk)
    return redirect(Post.objects.get(pk=pk).get_absolute_url())


def unlike_post_view(request: HttpRequest, pk: int):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        like = Like.objects.get(author_id=request.user.id, post_id=pk)
        like.delete()
    except Like.DoesNotExist:
        pass
    return redirect(Post.objects.get(pk=pk).get_absolute_url())


def share_post_view(request: HttpRequest, pk: int):
    orignal_post = Post.objects.get(pk=pk)
    orignal_post.pk = None
    new_post = Post.objects.create(
        title=orignal_post.title,
        description=orignal_post.description,
        content_type=orignal_post.content_type,
        content=orignal_post.content,
        author_id=request.user.id,
        shared_author=orignal_post.author,
        unlisted=orignal_post.unlisted,
        date_published=orignal_post.date_published
    )
    new_post.save()

    return redirect(new_post.get_absolute_url())


def like_comment_view(request: HttpRequest, post_pk: int, pk: int):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    comment_like, created = CommentLike.objects.get_or_create(author_id=request.user.id, comment_id=pk)
    return redirect(Post.objects.get(pk=post_pk).get_absolute_url())


def unlike_comment_view(request: HttpRequest, post_pk: int, pk: int):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        like = CommentLike.objects.get(author_id=request.user.id, comment_id=pk)
        like.delete()
    except Like.DoesNotExist:
        pass
    return redirect(Post.objects.get(pk=post_pk).get_absolute_url())
