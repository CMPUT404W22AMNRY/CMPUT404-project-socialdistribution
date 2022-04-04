from django.urls import path
from .views import (
    FriendRequestsView,
    MyFriendsView,
    create_follow_request,
    accept_follow_request,
    unfollow_request,
    reject_follow_request,
    remote_friend_request,
    remote_unfollow,
    accept_remote_follow_request,
    reject_remote_follow_request,
    UsersView
)

app_name = 'follow'
urlpatterns = [
    path('users/<slug:to_username>/request/', view=create_follow_request, name='create_follow_request'),
    path('users/<slug:from_username>/accept/', view=accept_follow_request, name='accept_follow_request'),
    path('users/<slug:from_username>/reject/', view=reject_follow_request, name='reject_follow_request'),
    path('users/<slug:from_username>/unfollow/', view=unfollow_request, name='unfollow_request'),
    path('remote/request/<path:url>/', view=remote_friend_request, name='remote_request'),
    path('remote/unfollow/<path:url>/', view=remote_unfollow, name='remote_unfollow'),
    path('remote/accept/<path:from_user_url>', view=accept_remote_follow_request, name='accept_remote_request'),
    path('remote/reject/<path:from_user_url>', view=reject_remote_follow_request, name='reject_remote_request'),
    path('friend-requests', view=FriendRequestsView.as_view(), name='friend_requests'),
    path('friends', view=MyFriendsView.as_view(), name='friends'),
    path('', view=UsersView.as_view(), name='users'),
]
