from django.http import HttpResponse
from django.test import TestCase, Client
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from api.tests.test_api import TEST_PASSWORD, TEST_USERNAME


class ViewsTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def signUpUser(self, username: str, password: str) -> HttpResponse:
        """
        Helper function to sign up user through sign up form
        """
        signup_data = {
            'username': username,
            'password1': password,
            'password2': password,
            'github_url': 'https://github.com/alice',
            'profile_image_url': 'https://imgur.com/alice.jpg',
        }
        return self.client.post(reverse_lazy('auth_provider:signup'), data=signup_data)

    def test_login_template(self):
        res = self.client.get(reverse_lazy('auth_provider:login'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed('auth/login.html')

    def test_signup_template(self):
        res = self.client.get(reverse_lazy('auth_provider:signup'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed('auth/signup.html')

    def test_signup_page(self):
        username = 'alice'
        password = 'L94C5fiBGYVLAxM'
        res = self.signUpUser(username, password)
        self.assertEqual(res.status_code, 302)
        self.assertIsNotNone(get_user_model()(username=username))

    def test_login_page(self):
        # Create user from admin to make user active by default
        username = 'alice'
        password = 'L94C5fiBGYVLAxM'
        get_user_model().objects.create_user(username=username, password=password)
        self.assertTrue(get_user_model()(username=username).is_active)

        login_data = {
            'username': username,
            'password': password,
        }
        res = self.client.post(reverse_lazy('auth_provider:login'), data=login_data)
        self.assertEqual(res.status_code, 302)

    def test_login_page_require_admin_approval(self):
        username = 'alice'
        password = 'L94C5fiBGYVLAxM'
        self.signUpUser(username, password)
        login_data = {
            'username': username,
            'password': password,
        }
        res = self.client.post(reverse_lazy('auth_provider:login'), data=login_data)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'error')


class ProfileTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.create_user(username=TEST_USERNAME, password=TEST_PASSWORD)
        self.user.first_name = 'Bob'
        self.user.last_name = 'Doyle'
        self.user.github_url = 'https://www.github.com/reillykeele'
        self.user.save()

    def test_my_profile(self):
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        res = self.client.get(reverse_lazy('auth_provider:my_profile'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'profile/my_profile.html')
