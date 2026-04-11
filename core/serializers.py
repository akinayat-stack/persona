from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Comment, Follow, Message, Post, Profile


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = fields


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user",
        write_only=True,
        required=False,
    )

    class Meta:
        model = Profile
        fields = ["id", "user", "user_id", "bio", "avatar", "created_at"]
        read_only_fields = ["id", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    author = UserSummarySerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="author",
        write_only=True,
        required=False,
    )
    likes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "author_id",
            "image",
            "caption",
            "created_at",
            "likes",
            "like_count",
            "comment_count",
        ]
        read_only_fields = ["id", "created_at", "likes", "like_count", "comment_count"]

    def validate(self, attrs):
        caption = attrs.get("caption", "")
        image = attrs.get("image")
        if not caption.strip() and not image:
            raise serializers.ValidationError("Either caption or image is required.")
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    author = UserSummarySerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="author",
        write_only=True,
        required=False,
    )
    post_id = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all(), source="post")

    class Meta:
        model = Comment
        fields = ["id", "post_id", "author", "author_id", "content", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty.")
        return value


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSummarySerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="sender",
        write_only=True,
        required=False,
    )
    receiver = UserSummarySerializer(read_only=True)
    receiver_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="receiver")
    likes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    like_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "sender_id",
            "receiver",
            "receiver_id",
            "content",
            "timestamp",
            "is_read",
            "likes",
            "like_count",
        ]
        read_only_fields = ["id", "timestamp", "likes", "like_count"]

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        return value

    def validate(self, attrs):
        sender = attrs.get("sender") or getattr(self.instance, "sender", None)
        receiver = attrs.get("receiver") or getattr(self.instance, "receiver", None)
        if sender and receiver and sender == receiver:
            raise serializers.ValidationError("Sender and receiver must be different users.")
        return attrs


class FollowSerializer(serializers.ModelSerializer):
    follower = UserSummarySerializer(read_only=True)
    follower_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="follower",
        write_only=True,
        required=False,
    )
    following = UserSummarySerializer(read_only=True)
    following_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source="following")

    class Meta:
        model = Follow
        fields = ["id", "follower", "follower_id", "following", "following_id", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        follower = attrs.get("follower") or getattr(self.instance, "follower", None)
        following = attrs.get("following") or getattr(self.instance, "following", None)
        if follower and following and follower == following:
            raise serializers.ValidationError("Users cannot follow themselves.")
        return attrs
