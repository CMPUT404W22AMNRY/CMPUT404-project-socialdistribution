from django.test import TestCase, Client
from django.urls import reverse_lazy


class ViewsTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_login_page(self):
        res = self.client.get(reverse_lazy('auth_provider:login'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed('auth/login.html')

    def test_signup_page(self):
        res = self.client.get(reverse_lazy('auth_provider:signup'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed('auth/signup.html')
