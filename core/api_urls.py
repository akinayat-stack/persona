from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_apiviews import (
    CommentDetailAPIView,
    CommentListCreateAPIView,
    FollowDetailAPIView,
    FollowListCreateAPIView,
    MessageDetailAPIView,
    MessageListCreateAPIView,
    PostDetailAPIView,
    PostListCreateAPIView,
    ProfileDetailAPIView,
    ProfileListCreateAPIView,
)
from .api_viewsets import (
    CommentViewSet,
    FollowViewSet,
    MessageViewSet,
    PostViewSet,
    ProfileViewSet,
)

router = DefaultRouter()
router.register("profiles", ProfileViewSet, basename="profiles")
router.register("posts", PostViewSet, basename="posts")
router.register("comments", CommentViewSet, basename="comments")
router.register("messages", MessageViewSet, basename="messages")
router.register("follows", FollowViewSet, basename="follows")

urlpatterns = [
    path("viewsets/", include(router.urls)),
    path("apiview/profiles/", ProfileListCreateAPIView.as_view(), name="apiview-profile-list"),
    path("apiview/profiles/<int:pk>/", ProfileDetailAPIView.as_view(), name="apiview-profile-detail"),
    path("apiview/posts/", PostListCreateAPIView.as_view(), name="apiview-post-list"),
    path("apiview/posts/<int:pk>/", PostDetailAPIView.as_view(), name="apiview-post-detail"),
    path("apiview/comments/", CommentListCreateAPIView.as_view(), name="apiview-comment-list"),
    path("apiview/comments/<int:pk>/", CommentDetailAPIView.as_view(), name="apiview-comment-detail"),
    path("apiview/messages/", MessageListCreateAPIView.as_view(), name="apiview-message-list"),
    path("apiview/messages/<int:pk>/", MessageDetailAPIView.as_view(), name="apiview-message-detail"),
    path("apiview/follows/", FollowListCreateAPIView.as_view(), name="apiview-follow-list"),
    path("apiview/follows/<int:pk>/", FollowDetailAPIView.as_view(), name="apiview-follow-detail"),
]
