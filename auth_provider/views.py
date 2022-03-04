from re import template
from django.forms import ModelForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from auth_provider.models import User
from .forms import SignUpForm


class SignUpView(CreateView):
    template_name = 'auth/signup.html'
    form_class = SignUpForm
    success_url = reverse_lazy('auth_provider:login')

