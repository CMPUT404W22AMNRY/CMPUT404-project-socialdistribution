from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Author


class SignUpForm(UserCreationForm):
    github_url = forms.CharField(max_length=512)
    profile_image_url = forms.CharField(max_length=512)

    def save(self, commit=True):
        user = super().save(commit)
        # Require server to set active manually by default
        user.is_active = False
        # Populate author related fields
        author = Author(
            user=user,
            github_url=self.cleaned_data['github_url'],
            profile_image_url=self.cleaned_data['profile_image_url'])
        if commit:
            author.save()
            user.save()
        return user
