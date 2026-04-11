from rest_framework import permissions, viewsets

from .models import Comment, Follow, Message, Post, Profile
from .serializers import (
    CommentSerializer,
    FollowSerializer,
    MessageSerializer,
    PostSerializer,
    ProfileSerializer,
)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.select_related("user").all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related("author").prefetch_related("likes", "comments")
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related("author", "post").all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.select_related("sender", "receiver").prefetch_related("likes")
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.select_related("follower", "following").all()
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
