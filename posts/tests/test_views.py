from .constants import COMMENT_DATA, COMMONMARK_POST_DATA, POST_DATA
from api.tests.test_api import TEST_PASSWORD, TEST_USERNAME
from api.tests.constants import SAMPLE_REMOTE_AUTHOR, SAMPLE_REMOTE_POST
from servers.models import Server
from requests import Response
from django.urls import reverse
from posts.models import CommentLike, Post, Category, ContentType, Comment, Like, RemoteComment
import json
from unittest.mock import MagicMock, patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model


EDITED_POST_DATA = POST_DATA.copy()
EDITED_POST_DATA['content_type'] = ContentType.MARKDOWN


class CreatePostViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        get_user_model().objects.create_user(username='bob', password='password')

    def test_new_post_page(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:new'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed('posts/create_post.html')

    def test_new_post_require_login(self):
        res = self.client.get(reverse('posts:new'))
        self.assertEqual(res.status_code, 302)

    def test_new_post_require_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username='bob', password='password')
        res = csrf_client.post(reverse('posts:new'), data=POST_DATA)
        self.assertEqual(res.status_code, 403)

    def test_new_post(self):
        self.client.login(username='bob', password='password')
        initial_post_count = len(Post.objects.all())
        self.client.post(reverse('posts:new'), data=POST_DATA)
        self.assertEqual(len(Post.objects.all()), initial_post_count + 1)

    def test_categories_not_duplicated(self):
        self.client.login(username='bob', password='password')
        Category.objects.create(category='web')
        initial_post_count = len(Post.objects.all())
        self.client.post(reverse('posts:new'), data=POST_DATA)
        self.assertEqual(len(Category.objects.all()), 2)
        self.assertEqual(len(Post.objects.all()), initial_post_count + 1)


class EditPostViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        current_user = 'bob'
        get_user_model().objects.create_user(username=current_user, password='password')

        # Create test post to edit
        post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=get_user_model().objects.get(
                username=current_user).id,
            unlisted=True)
        post.save()
        self.post_id = post.id

    def test_edit_post_page(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:edit', kwargs={'pk': self.post_id}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed('posts/edit_post.html')

    def test_edit_post_require_login(self):
        res = self.client.get(reverse('posts:edit', kwargs={'pk': self.post_id}))
        self.assertEqual(res.status_code, 302)

    def test_edit_post_require_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username='bob', password='password')
        res = csrf_client.post(reverse('posts:edit', kwargs={'pk': self.post_id}), data=EDITED_POST_DATA)
        self.assertEqual(res.status_code, 403)

    def test_edit_post(self):
        self.client.login(username='bob', password='password')
        res = self.client.post(reverse('posts:edit', kwargs={'pk': self.post_id}), data=EDITED_POST_DATA)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Post.objects.get(pk=self.post_id).content_type, EDITED_POST_DATA['content_type'])

    def test_edit_non_existing_post(self):
        self.client.login(username='bob', password='password')
        res = self.client.post(reverse('posts:edit', kwargs={'pk': 900}), data=EDITED_POST_DATA)
        self.assertEqual(res.status_code, 404)

    def test_edit_page_as_another_user(self):
        username = 'alice'
        password = TEST_PASSWORD
        get_user_model().objects.create_user(username=username, password=password)

        self.client.login(username=username, password=password)
        res = self.client.get(reverse('posts:edit', kwargs={'pk': self.post_id}))
        self.assertEqual(res.status_code, 403)

    def test_edit_as_another_user(self):
        username = 'alice'
        password = TEST_PASSWORD
        get_user_model().objects.create_user(username=username, password=password)

        self.client.login(username=username, password=password)
        res = self.client.post(reverse('posts:edit', kwargs={'pk': self.post_id}), data=EDITED_POST_DATA)
        self.assertEqual(res.status_code, 403)


class PostDetailViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='bob', password='password')
        self.post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=self.user.id,
            unlisted=True)
        self.post2 = Post.objects.create(
            title=COMMONMARK_POST_DATA['title'],
            description=COMMONMARK_POST_DATA['description'],
            content_type=COMMONMARK_POST_DATA['content_type'],
            content=COMMONMARK_POST_DATA['content'],
            author_id=self.user.id,
            unlisted=True)
        self.post.save()

    def test_detail_view_page(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:detail', kwargs={'pk': self.post.id}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'posts/post_detail.html')
        self.assertContains(res, self.post.title)
        self.assertContains(res, self.post.author.get_full_name())
        self.assertContains(res, self.post.content)
        for category in self.post.categories.all():
            self.assertContains(res, category.category)

    def test_comments_section(self):
        for _ in range(3):
            comment = Comment.objects.create(
                comment=COMMENT_DATA['comment'],
                author=self.user,
                content_type=COMMENT_DATA['content_type'],
                post=self.post,
            )
            comment.save()

        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:detail', kwargs={'pk': self.post.id}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Comments')
        self.assertContains(res, COMMENT_DATA['comment'], count=3)

    def test_like_section(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:detail', kwargs={'pk': self.post.id}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Like')

    def test_like(self):
        self.client.login(username='bob', password='password')
        res = self.client.post(reverse('posts:like', kwargs={'pk': self.post.id}))
        self.assertEqual(res.status_code, 302)
        self.assertIsNotNone(Like.objects.get(author=self.user, post=self.post))

    def test_like_require_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username='bob', password='password')
        res = csrf_client.post(reverse('posts:like', kwargs={'pk': self.post.id}))
        self.assertEqual(res.status_code, 403)

    def test_disable_like(self):
        Like.objects.create(author=self.user, post=self.post)
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:detail', kwargs={'pk': self.post.id}))
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'Like')

    def test_commonmark(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:detail', kwargs={'pk': self.post2.id}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '<h1>Heading 8-)</h1>')
        self.assertContains(res, '<p><strong>This is bold text!</strong></p>')

    def test_like_comment(self):
        comment = Comment.objects.create(
            comment=COMMENT_DATA['comment'],
            author=self.user,
            content_type=COMMENT_DATA['content_type'],
            post=self.post,
        )
        comment.save()

        self.assertEqual(len(comment.commentlike_set.all()), 0)

        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        res = self.client.post(reverse('posts:like-comment', kwargs={'post_pk': self.post.id, 'pk': comment.id}))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(len(comment.commentlike_set.all()), 1)

    def test_unlike_comment(self):
        comment = Comment.objects.create(
            comment=COMMENT_DATA['comment'],
            author=self.user,
            content_type=COMMENT_DATA['content_type'],
            post=self.post,
        )
        comment.save()
        comment_like = CommentLike.objects.create(
            author=self.user,
            comment=comment
        )
        comment_like.save()

        self.assertEqual(len(comment.commentlike_set.all()), 1)

        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        res = self.client.post(reverse('posts:unlike-comment', kwargs={'post_pk': self.post.id, 'pk': comment.id}))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(len(comment.commentlike_set.all()), 0)

    def test_share_post(self):
        alice = get_user_model().objects.create_user(username='alice', password='password')
        self.client.login(username=alice.username, password=alice.password)
        self.post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=alice.id,
            unlisted=True)
        self.post.save()
        initial_post_count = len(Post.objects.all())

        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        self.shared_post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=alice.id,
            shared_author=self.user,
            unlisted=True)
        self.shared_post.save()
        res = self.client.get(reverse('posts:my-posts'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(Post.objects.all()), initial_post_count + 1)

    def test_contains_remote_comments(self):
        author = json.loads(SAMPLE_REMOTE_AUTHOR)
        author_url = author.get('url')
        remote_comment = RemoteComment.objects.create(
            comment=COMMENT_DATA['comment'],
            author_url=author_url,
            content_type=COMMENT_DATA['content_type'],
            post=self.post,
        )
        remote_comment.save()

        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)

        mock_response = Response()
        mock_response.json = MagicMock(return_value=author)

        mock_server = Server(
            service_address="https://cmput-404-w22-project-group09.herokuapp.com/service",
            username="hello",
            password="no",
        )
        mock_server.get = MagicMock(return_value=mock_response)

        with patch('servers.models.Server.objects') as MockServerObjects:
            MockServerObjects.all.return_value = [mock_server]

            self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
            res = self.client.get(reverse('posts:detail', kwargs={'pk': self.post.id}))

            remote_comment_count = len(RemoteComment.objects.filter(post=self.post))
            self.assertTemplateUsed(res, 'posts/partials/_remote_comment.html', count=remote_comment_count)


class RemotePostDetailView(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username=TEST_USERNAME, password=TEST_PASSWORD)

    def test_remote_detail_view_page(self):
        mock_json_response = json.loads(SAMPLE_REMOTE_POST)
        mock_response = Response()
        mock_response.json = MagicMock(return_value=mock_json_response)

        mock_server = Server(
            service_address="http://localhost:5555/api/v2",
            username="hello",
            password="no",
        )
        mock_server.get = MagicMock(return_value=mock_response)

        with patch('servers.models.Server.objects') as MockServerObjects:
            MockServerObjects.all.return_value = [mock_server]

            self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
            res = self.client.get(
                reverse(
                    'posts:remote-detail',
                    kwargs={
                        'url': 'http://localhost:5555/api/v2/authors/1/posts/1/'}))
            self.assertEqual(res.status_code, 200)

            self.assertContains(res, mock_json_response['title'])
            self.assertContains(res, mock_json_response['author']['display_name'])

    def test_contains_remote_comments(self):
        mock_json_response = json.loads(SAMPLE_REMOTE_POST)
        mock_response = Response()
        mock_response.json = MagicMock(return_value=mock_json_response)

        mock_server = Server(
            service_address="http://localhost:5555/api/v2",
            username="hello",
            password="no",
        )
        mock_server.get = MagicMock(return_value=mock_response)

        with patch('servers.models.Server.objects') as MockServerObjects:
            MockServerObjects.all.return_value = [mock_server]

            self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
            res = self.client.get(
                reverse(
                    'posts:remote-detail',
                    kwargs={
                        'url': 'http://localhost:5555/api/v2/authors/1/posts/1/'}))
            self.assertEqual(res.status_code, 200)
            self.assertTemplateUsed(res, 'posts/partials/_remote_comment.html')

            for comment in mock_json_response['comment_src']:
                self.assertContains(res, comment['comment'])
                self.assertContains(res, comment['published'])
                self.assertContains(res, comment['author']['display_name'])


class PostDeleteViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='bob', password='password')
        self.post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=self.user.id,
            unlisted=True)
        self.post.save()

    def test_post_delete_view_page(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:delete', kwargs={'pk': self.post.id}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'posts/delete_post.html')
        self.assertContains(res, self.post.title)

    def test_post_delete_view(self):
        initial_post_count = len(Post.objects.all())
        self.client.login(username='bob', password='password')
        res = self.client.post(reverse('posts:delete', kwargs={'pk': self.post.id}))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(len(Post.objects.all()), initial_post_count - 1)


class CreateCommentViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='bob', password='password')
        self.post = Post.objects.create(
            title=POST_DATA['title'],
            description=POST_DATA['description'],
            content_type=POST_DATA['content_type'],
            content=POST_DATA['content'],
            author_id=self.user.id,
            unlisted=True)
        self.post.save()

    def test_new_comment_page(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:new-comment', kwargs={'pk': self.post.id}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'comments/create_comment.html')

    def test_new_comment(self):
        self.client.login(username='bob', password='password')
        res = self.client.post(reverse('posts:new-comment', kwargs={'pk': self.post.id}), data=COMMENT_DATA)
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, reverse('posts:detail', kwargs={'pk': self.post.id}))
        self.assertEqual(len(self.post.comment_set.all()), 1)

    def test_new_comment_require_login(self):
        res = self.client.get(reverse('posts:edit', kwargs={'pk': self.post.id}))
        self.assertEqual(res.status_code, 302)

    def test_new_comment_require_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username='bob', password='password')
        res = csrf_client.post(reverse('posts:new-comment', kwargs={'pk': self.post.id}), data=COMMENT_DATA)
        self.assertEqual(res.status_code, 403)


class MyPostsViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='bob', password='password')
        alice = get_user_model().objects.create_user(username='alice', password='password')
        self.posts: list[Post] = []
        self.posts_per_user = 2

        for user in [self.user, alice]:
            for _ in range(self.posts_per_user):
                post = Post.objects.create(
                    title=POST_DATA['title'],
                    description=POST_DATA['description'],
                    content_type=POST_DATA['content_type'],
                    content=POST_DATA['content'],
                    author_id=user.id,
                    unlisted=True)
                post.save()

    def test_post_list_page(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:my-posts'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'posts/post_list.html')

    def test_post_list_empty_page(self):
        Post.objects.filter(author=self.user).delete()
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:my-posts'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'No posts yet')

    def test_post_list(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('posts:my-posts'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, POST_DATA['title'], self.posts_per_user)

    def test_new_comment_require_login(self):
        res = self.client.get(reverse('posts:my-posts'))
        self.assertEqual(res.status_code, 302)
