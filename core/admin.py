from django.contrib import admin
from .models import Profile, Post, Comment, Message, Follow


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    search_fields = ['user__username']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'is_text_only', 'created_at', 'like_count']
    list_filter = ['created_at']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'content', 'created_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'timestamp', 'is_read', 'like_count']
    list_filter = ['is_read', 'timestamp']
