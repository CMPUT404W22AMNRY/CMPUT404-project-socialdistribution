from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit)
        # Require server to set active manually by default
        user.is_active = False
        if commit:
            user.save()
        return user
