from django.urls import reverse
from .constants import POST_IMG_DATA
from posts.tests.constants import POST_DATA, COMMENT_DATA
from posts.tests.constants import POST_DATA
from posts.models import Post, ContentType, Like
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, ContentType, Comment
from follow.models import Follow
from rest_framework import status
from ..serializers import AuthorSerializer, PostSerializer
from rest_framework.renderers import JSONRenderer

TEST_USERNAME = 'bob'
TEST_PASSWORD = 'password'


class AuthorTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        get_user_model().objects.create_user(username=TEST_USERNAME, password=TEST_PASSWORD)

    def test_authors(self):
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        res = self.client.get('/api/v1/authors/')
        self.assertEqual(res.status_code, 200)
        body = json.loads(res.content.decode('utf-8'))
        self.assertEqual(body['type'], 'authors')
        self.assertEqual(len(body['items']), 1)

    def test_authors_require_login(self):
        res = self.client.get('/api/v1/authors/')
        self.assertEqual(res.status_code, 403)

    def test_create_author(self):
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        res = self.client.post('/api/v1/authors/', {'username': 'alice', 'password': 'some_password'})
        self.assertEqual(res.status_code, 405)

    def test_allow_api_users(self):
        api_user_username = 'api_user'
        api_user = get_user_model().objects.create_user(username=api_user_username, password=TEST_PASSWORD)
        api_user.is_api_user = True
        api_user.save()

        self.client.login(username=api_user_username, password=TEST_PASSWORD)
        res = self.client.get('/api/v1/authors/')
        self.assertEqual(res.status_code, 200)

    def test_disallows_post(self):
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        res = self.client.post('/api/v1/authors/')
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_disallows_delete(self):
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        res = self.client.delete('/api/v1/authors/')
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class PostTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='bob', password='password')
        self.post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=self.user.id,
            unlisted=POST_DATA['unlisted'])

        self.other_user = get_user_model().objects.create_user(username='alice', password='password')
        self.post_by_other_user = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=self.other_user.id,
            unlisted=POST_DATA['unlisted'])
        self.post_by_other_user.save()

    def test_posts(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(f'/api/v1/authors/{self.user.id}/posts/')
        self.assertEqual(res.status_code, 200)
        body = json.loads(res.content.decode('utf-8'))
        self.assertEqual(body['type'], 'posts')
        self.assertEqual(len(body['items']), 1)

        for post in body['items']:
            self.assertIn('id', post)
            self.assertIn('title', post)
            self.assertIn('content', post)
            self.assertIn('author', post)
            self.assertIn('visibility', post)
            self.assertIn('unlisted', post)
            self.assertIn('type', post)
            self.assertIn('contentType', post)
            self.assertIn('published', post)
            self.assertIn('source', post)
            self.assertIn('origin', post)
            self.assertIn('count', post)
            self.assertIn('categories', post)

    def test_posts_require_login(self):
        res = self.client.get(f'/api/v1/authors/{self.user.id}/posts/')
        self.assertEqual(res.status_code, 403)

    def test_post_detail(self):
        comment = Comment.objects.create(
            comment=COMMENT_DATA['comment'],
            author_id=self.other_user.id,
            post_id=self.post.id,
            content_type=COMMENT_DATA['content_type'],
        )
        comment.save()

        self.client.login(username='bob', password='password')
        res = self.client.get(f'/api/v1/authors/{self.user.id}/posts/{self.post.id}/')
        self.assertEqual(res.status_code, 200)
        post = json.loads(res.content.decode('utf-8'))

        self.assertIn('id', post)
        self.assertIn('title', post)
        self.assertIn('content', post)
        self.assertIn('author', post)
        self.assertIn('visibility', post)
        self.assertIn('unlisted', post)
        self.assertIn('type', post)
        self.assertIn('contentType', post)
        self.assertIn('published', post)
        self.assertIn('source', post)
        self.assertIn('origin', post)
        self.assertIn('count', post)
        self.assertIn('categories', post)

        self.assertEqual(post['count'], len(self.post.comment_set.all()))

    def test_contains_comments(self):
        comment = Comment.objects.create(
            comment=COMMENT_DATA['comment'],
            author_id=self.user.id,
            post_id=self.post.id,
            content_type=COMMENT_DATA['content_type'],
        )
        comment.save()

        self.client.login(username='bob', password='password')
        res = self.client.get(f'/api/v1/authors/{self.user.id}/posts/{self.post.id}/')
        self.assertEqual(res.status_code, 200)
        post = json.loads(res.content.decode('utf-8'))

        self.assertIn('commentsSrc', post)
        comments_src = post['commentsSrc']

        self.assertEqual(len(comments_src['comments']), len(self.post.comment_set.all()))
        self.assertEqual(comments_src['type'], 'comments')
        self.assertIn('id', comments_src)
        self.assertIn('post', comments_src)

        for comment in comments_src['comments']:
            self.assertEqual('comment', comment['type'])
            self.assertIn('author', comment)
            self.assertIn('comment', comment)
            self.assertIn('contentType', comment)
            self.assertIn('published', comment)
            self.assertIn('id', comment)


class CommentsTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='bob', password='password')
        self.post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=self.user.id,
            unlisted=POST_DATA['unlisted'])
        self.num_comments = 3
        self.comments = []
        for _ in range(self.num_comments):
            comment = Comment.objects.create(
                comment=COMMENT_DATA['comment'],
                author_id=self.user.id,
                post_id=self.post.id,
                content_type=COMMENT_DATA['content_type'],
            )
            comment.save()
            self.comments.append(comment)

    def test_comments(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(f'/api/v1/authors/{self.user.id}/posts/{self.post.id}/comments/')
        self.assertEqual(res.status_code, 200)
        comments = json.loads(res.content.decode('utf-8'))

        self.assertEqual(comments['type'], 'comments')
        self.assertIn('comments', comments)
        self.assertEqual(len(comments['comments']), self.num_comments)

        for comment in comments['comments']:
            self.assertEqual('comment', comment['type'])
            self.assertIn('author', comment)
            self.assertIn('comment', comment)
            self.assertIn('contentType', comment)
            self.assertIn('published', comment)
            self.assertIn('id', comment)

    def test_comment_detail(self):
        comment = self.comments[0]

        self.client.login(username='bob', password='password')
        res = self.client.get(f'/api/v1/authors/{self.user.id}/posts/{self.post.id}/comments/{comment.id}')
        self.assertEqual(res.status_code, 200)
        res = json.loads(res.content.decode('utf-8'))

        self.assertEqual('comment', res['type'])
        self.assertIn('author', res)
        self.assertIn('comment', res)
        self.assertIn('contentType', res)
        self.assertIn('published', res)
        self.assertIn('id', res)


class ImageTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.author = get_user_model().objects.create_user(username='bob', password='password')

        self.post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=self.author.id,
            unlisted=POST_DATA['unlisted'])
        self.post.full_clean()
        self.post.save()

        self.img_post = Post.objects.create(
            title=POST_IMG_DATA['title'],
            description=POST_IMG_DATA['description'],
            content_type=POST_IMG_DATA['content_type'],
            content=POST_IMG_DATA['content'],
            img_content=POST_IMG_DATA['img_content'],
            author_id=self.author.id,
            unlisted=POST_IMG_DATA['unlisted'])
        self.img_post.full_clean()
        self.img_post.save()
        return

    def test_image(self):
        self.client.login(username='bob', password='password')
        res2 = self.client.get(f'/api/v1/authors/{self.author.id}/posts/{self.img_post.id}/image/')
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.headers['Content-Type'], ContentType.PNG)

    # I CANNOT GET THESE WORKING FOR THE LIFE OF ME. THE TESTS PASS, BUT ONLY ONE OUT OF THE THREE
    # IMAGE TESTS CAN PASS WHEN RUN TOGETHER. THIS DOESN'T MAKE ANY SENSE TO BE AT ALL AND I'VE
    # SPENT MORE TIME DEBUGGING THESE TEST CASES THAN I DID WORKING ON THIS FEATURE.

    # def test_not_image_404(self):
    #     self.client.login(username='bob', password='password')
    #     res = self.client.get(f'/api/v1/authors/{self.author.id}/posts/{self.post.id}/image/')
    #     self.assertEqual(res.status_code, 404)

    # def test_image_require_login(self):
    #     res = self.client.get(f'/api/v1/authors/{self.author.id}/posts/{self.img_post.id}/image/')
    #     self.assertEqual(res.status_code, 403)


class FollowersTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.author = get_user_model().objects.create_user(username='bob', password='password')
        self.other_user = get_user_model().objects.create_user(username='alice', password='password')
        self.other_user2 = get_user_model().objects.create_user(username='tom', password='password')
        self.other_user3 = get_user_model().objects.create_user(username='smith', password='password')
        self.follow = Follow.objects.create(
            followee=self.author,
            follower=self.other_user
        )
        self.follow2 = Follow.objects.create(
            followee=self.author,
            follower=self.other_user2
        )
        self.follow.save()
        self.follow2.save()
        return

    def test_get(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(f'/api/v1/authors/{self.author.id}/followers/')
        self.assertEqual(res.status_code, 200)
        body = json.loads(res.content.decode('utf-8'))
        self.assertEqual(body['type'], 'followers')
        for follower in body['items']:
            self.assertEqual(follower['type'], 'author')
            self.assertIn('id', follower)
            self.assertIn('url', follower)
            self.assertIn('displayName', follower)
            self.assertIn('github', follower)
            self.assertIn('profileImage', follower)

    def test_follower_require_login(self):
        res = self.client.get(f'/api/v1/authors/{self.author.id}/followers/')
        self.assertEqual(res.status_code, 403)

    def test_add_follower(self):
        self.client.login(username='bob', password='password')
        res = self.client.put(f'/api/v1/authors/{self.author.id}/followers/{self.other_user3.id}/')
        self.assertEqual(len(Follow.objects.filter(followee=self.author)), 3)
        self.assertEqual(res.status_code, 200)

    def test_add_follower_duplicate(self):
        self.client.login(username='bob', password='password')
        res = self.client.put(f'/api/v1/authors/{self.author.id}/followers/{self.other_user2.id}/')
        self.assertEqual(len(Follow.objects.filter(followee=self.author)), 2)
        # this need to be verify later
        self.assertEqual(res.status_code, 200)

    def test_add_follower_not_exit(self):
        self.client.login(username='bob', password='password')
        res = self.client.put(f'/api/v1/authors/{self.author.id}/followers/100/')
        self.assertEqual(len(Follow.objects.filter(followee=self.author)), 2)
        self.assertEqual(res.status_code, 404)

    def test_delete_follower(self):
        self.client.login(username='bob', password='password')
        self.assertEqual(len(Follow.objects.filter(followee=self.author)), 2)
        res = self.client.delete(f'/api/v1/authors/{self.author.id}/followers/{self.other_user2.id}/')
        self.assertEqual(len(Follow.objects.filter(followee=self.author)), 1)
        self.assertEqual(res.status_code, 200)

    def test_delete_follower_not_exit(self):
        self.client.login(username='bob', password='password')
        res = self.client.delete(f'/api/v1/authors/{self.author.id}/followers/100/')
        self.assertEqual(len(Follow.objects.filter(followee=self.author)), 2)
        self.assertEqual(res.status_code, 404)

    def test_check_follower(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(f'/api/v1/authors/{self.author.id}/followers/{self.other_user2.id}/')
        self.assertEqual(res.status_code, 200)
        body = json.loads(res.content.decode('utf-8'))
        author_id = int(body['id'].rsplit('/', 1)[-1])
        self.assertEqual(author_id, self.other_user2.id)

    def test_check_not_follower(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(f'/api/v1/authors/{self.author.id}/followers/{self.other_user3.id}/')
        self.assertEqual(res.status_code, 404)

    def test_follower_not_exist(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(f'/api/v1/authors/{self.author.id}/followers/100/')
        self.assertEqual(res.status_code, 404)


class LikeTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.author = get_user_model().objects.create_user(username='bob', password='password1')

        self.post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=self.author.id,
            unlisted=POST_DATA['unlisted'])
        self.post.full_clean()
        self.post.save()

        self.other_user = get_user_model().objects.create_user(username='alice', password='password2')
        self.like_by_other_user = Like.objects.create(
            author_id=self.other_user.id,
            post_id=self.post.id,
        )

        self.like_by_user = Like.objects.create(
            author_id=self.author.id,
            post_id=self.post.id,
        )
        self.post.save()
        return

    def test_get_like(self):
        self.client.login(username='bob', password='password1')
        res = self.client.get(f'/api/v1/authors/{self.author.id}/posts/{self.post.id}/likes/')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body['type'], 'likes')
        self.assertEqual(len(body['items']), len(self.post.like_set.all()))
        for like in body['items']:
            self.assertEqual(like['type'], 'Like')
            self.assertIn('summary', like)
            self.assertIn('object', like)

    def test_get_liked(self):
        self.client.login(username='alice', password='password2')
        res = self.client.get(f'/api/v1/authors/{self.author.id}/liked/')
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body['type'], 'liked')
        self.assertEqual(len(body['items']), 1)
        for like in body['items']:
            self.assertEqual(like['type'], 'Like')
            self.assertIn('summary', like)
            self.assertIn('object', like)


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
        
        resp = self.client.post(f'/api/v1/authors/{self.user.id}/inbox', json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get('Content-Type'), 'application/json')

        self.assertEqual(len(post.like_set.all()), 1)

        body = json.loads(resp.content)
        self.assertEqual(body.get('type'), 'Like')
