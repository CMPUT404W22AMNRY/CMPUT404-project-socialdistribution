from django.test import TestCase, Client
from django.contrib.auth.models import User


class PostTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        User.objects.create_user(username='bob', password='password')

    def test_new_post(self):
        self.client.login(username='bob', password='password')
        res = self.client.get('/posts/new')
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed('posts/post_form.html')


    def test_new_post_require_login(self):
        res = self.client.get('/posts/new')
        self.assertEqual(res.status_code, 302)

