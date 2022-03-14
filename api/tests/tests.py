import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from posts.models import Post, ContentType

from .constants import POST_IMG_DATA


class AuthorTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        get_user_model().objects.create_user(username='bob', password='password')

    def test_authors(self):
        self.client.login(username='bob', password='password')
        res = self.client.get('/api/v1/authors/')
        self.assertEqual(res.status_code, 200)
        body = json.loads(res.content.decode('utf-8'))
        self.assertEqual(body['type'], 'authors')
        self.assertEqual(len(body['items']), 1)

    def test_authors_require_login(self):
        res = self.client.get('/api/v1/authors/')
        self.assertEqual(res.status_code, 403)

    def test_create_author(self):
        self.client.login(username='bob', password='password')
        res = self.client.post('/api/v1/authors/', {'username': 'alice', 'password': 'password'})
        self.assertEqual(res.status_code, 405)


class ImageTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.author = get_user_model().objects.create_user(username='bob', password='password')

        self.post = Post.objects.create(
            title=POST_IMG_DATA['title'],
            description=POST_IMG_DATA['description'],
            content_type=POST_IMG_DATA['content_type'],
            content=POST_IMG_DATA['content'],
            img_content=POST_IMG_DATA['img_content'],
            author_id=self.author.id,
            unlisted=POST_IMG_DATA['unlisted'])
        self.post.full_clean()
        self.post.save()

        return

    def test_image(self):
        self.client.login(username='bob', password='password')
        res2 = self.client.get(f'/api/v1/authors/{self.author.id}/posts/{self.post.id}/image/')
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.headers['Content-Type'], ContentType.PNG)
