from django.test import TestCase, Client
from django.contrib.auth.models import User


class AuthorTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        User.objects.create_user(username='bob', password='password')

    def test_authors(self):
        self.client.login(username='bob', password='password')
        res = self.client.get('/api/v1/authors/')
        self.assertEqual(res.status_code, 200)

    def test_authors_require_login(self):
        res = self.client.get('/api/v1/authors/')
        self.assertEqual(res.status_code, 403)
