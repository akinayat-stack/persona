from django.http import Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment, Follow, Message, Post, Profile
from .serializers import (
    CommentSerializer,
    FollowSerializer,
    MessageSerializer,
    PostSerializer,
    ProfileSerializer,
)


class BaseListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    model = None
    serializer_class = None
    select_related = ()
    prefetch_related = ()

    def get_queryset(self):
        queryset = self.model.objects.all()
        if self.select_related:
            queryset = queryset.select_related(*self.select_related)
        if self.prefetch_related:
            queryset = queryset.prefetch_related(*self.prefetch_related)
        return queryset

    def get(self, request):
        serializer = self.serializer_class(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BaseDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    model = None
    serializer_class = None
    select_related = ()
    prefetch_related = ()

    def get_queryset(self):
        queryset = self.model.objects.all()
        if self.select_related:
            queryset = queryset.select_related(*self.select_related)
        if self.prefetch_related:
            queryset = queryset.prefetch_related(*self.prefetch_related)
        return queryset

    def get_object(self, pk):
        try:
            return self.get_queryset().get(pk=pk)
        except self.model.DoesNotExist as exc:
            raise Http404 from exc

    def get(self, request, pk):
        serializer = self.serializer_class(self.get_object(pk))
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        instance = self.get_object(pk)
        serializer = self.serializer_class(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        instance = self.get_object(pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileListCreateAPIView(BaseListCreateAPIView):
    model = Profile
    serializer_class = ProfileSerializer
    select_related = ("user",)


class ProfileDetailAPIView(BaseDetailAPIView):
    model = Profile
    serializer_class = ProfileSerializer
    select_related = ("user",)


class PostListCreateAPIView(BaseListCreateAPIView):
    model = Post
    serializer_class = PostSerializer
    select_related = ("author",)
    prefetch_related = ("likes", "comments")


class PostDetailAPIView(BaseDetailAPIView):
    model = Post
    serializer_class = PostSerializer
    select_related = ("author",)
    prefetch_related = ("likes", "comments")


class CommentListCreateAPIView(BaseListCreateAPIView):
    model = Comment
    serializer_class = CommentSerializer
    select_related = ("author", "post")


class CommentDetailAPIView(BaseDetailAPIView):
    model = Comment
    serializer_class = CommentSerializer
    select_related = ("author", "post")


class MessageListCreateAPIView(BaseListCreateAPIView):
    model = Message
    serializer_class = MessageSerializer
    select_related = ("sender", "receiver")
    prefetch_related = ("likes",)


class MessageDetailAPIView(BaseDetailAPIView):
    model = Message
    serializer_class = MessageSerializer
    select_related = ("sender", "receiver")
    prefetch_related = ("likes",)


class FollowListCreateAPIView(BaseListCreateAPIView):
    model = Follow
    serializer_class = FollowSerializer
    select_related = ("follower", "following")


class FollowDetailAPIView(BaseDetailAPIView):
    model = Follow
    serializer_class = FollowSerializer
    select_related = ("follower", "following")
