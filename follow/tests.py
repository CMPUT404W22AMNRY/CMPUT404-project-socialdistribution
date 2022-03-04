from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Follow


class FriendRequestsViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.bob = get_user_model().objects.create_user(username='bob', password='password')
        self.alice = get_user_model().objects.create_user(username='alice', password='password')

    def test_friend_requests_page(self):
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('follow:friend_requests'))

        self.assertTemplateUsed(res, 'follow/request_list.html')

    def test_friend_requests(self):
        Follow.objects.follow_request(from_user=self.alice, to_user=self.bob)
        self.client.login(username='bob', password='password')
        res = self.client.get(reverse('follow:friend_requests'))

        self.assertContains(res, self.alice.username)
