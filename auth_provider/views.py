from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm


class SignUpView(CreateView):
    template_name = 'auth/signup.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
