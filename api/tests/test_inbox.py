import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from rest_framework import status

from .constants import SAMPLE_REMOTE_AUTHOR
from .test_api import TEST_PASSWORD, TEST_USERNAME
from posts.models import Post
from posts.tests.constants import POST_DATA
from posts.tests.constants import POST_DATA

class InboxTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.create_user(username=TEST_USERNAME, password=TEST_PASSWORD)

    def test_get(self):
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        res = self.client.get(f'/api/v1/authors/{self.user.id}/inbox')
        self.assertEqual(res.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def test_post(self):
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        res = self.client.post(f'/api/v1/authors/{self.user.id}/inbox')
        self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_delete(self):
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        res = self.client.delete(f'/api/v1/authors/{self.user.id}/inbox')
        self.assertEqual(res.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def test_like(self):
        post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=self.user.id,
            unlisted=POST_DATA['unlisted'])
        post.save()

        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        author_response = self.client.get(f'/api/v1/authors/{self.user.id}').content
        post_response = self.client.get(f'/api/v1/authors/{self.user.id}/posts/{post.id}').content
        post_url = json.loads(post_response).get('id')

        payload = {
            'type': 'Like',
            'author': json.loads(author_response),
            'object': post_url
        }

        self.assertEqual(len(post.like_set.all()), 0)

        resp = self.client.post(
            f'/api/v1/authors/{self.user.id}/inbox',
            json.dumps(payload),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get('Content-Type'), 'application/json')

        self.assertEqual(len(post.like_set.all()), 1)

        body = json.loads(resp.content)
        self.assertEqual(body.get('type'), 'Like')

    def test_remote_like(self):
        post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=self.user.id,
            unlisted=POST_DATA['unlisted'])
        post.save()

        self.assertEqual(len(post.remotelike_set.all()), 0)

        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        post_response = self.client.get(f'/api/v1/authors/{self.user.id}/posts/{post.id}').content
        post_url = json.loads(post_response).get('id')

        payload = {
            'type': 'Like',
            'author': json.loads(SAMPLE_REMOTE_AUTHOR),
            'object': post_url
        }

        resp = self.client.post(
            f'/api/v1/authors/{self.user.id}/inbox',
            json.dumps(payload),
            content_type='application/json')
        self.assertEqual(resp.status_code, 204)

        self.assertEqual(len(post.remotelike_set.all()), 1)
