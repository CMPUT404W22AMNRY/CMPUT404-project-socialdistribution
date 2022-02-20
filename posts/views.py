from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import ModelForm
from django.views.generic.edit import CreateView
from posts.models import Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        exclude = ['author', 'categories']


class CreatePostView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm

    def form_valid(self, form: PostForm):
        form.instance.author = self.request.user
        return super().form_valid(form)
