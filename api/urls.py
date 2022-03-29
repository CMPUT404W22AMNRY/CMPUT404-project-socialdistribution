from django.urls import include, path
from rest_framework import routers
from api.views import AuthorViewSet, CommentViewSet, PostViewSet, LikesViewSet, LikedViewSet
from api.views import AuthorViewSet, PostViewSet, FollowersViewSet
from rest_framework_nested import routers


class OptionalSlashRouter(routers.DefaultRouter):
    def __init__(self):
        super().__init__()
        self.trailing_slash = '/?'


router = OptionalSlashRouter()
router.register(r'authors', AuthorViewSet)

author_router = routers.NestedDefaultRouter(router, r'authors', lookup='author')
author_router.register(r'posts', PostViewSet, basename='post')
author_router.register(r'followers', FollowersViewSet, basename='follower')
author_router.register(r'liked', LikedViewSet, basename='liked')

post_router = routers.NestedDefaultRouter(author_router, r'posts', lookup='post')
post_router.register(r'likes', LikesViewSet, basename='likes')
post_router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(author_router.urls)),
    path('', include(post_router.urls))
]
