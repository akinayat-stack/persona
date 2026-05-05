# core/models.py
# Persona — Social Media Application
# Models following Django MVT architecture with PostgreSQL backend

from django.db import models
from django.contrib.auth.models import User


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return f"https://ui-avatars.com/api/?name={self.user.username}&background=1D6AE5&color=fff&size=128"

    def post_count(self):
        return self.user.posts.count()


class Post(BaseModel):
    """
    Supports both image posts and text-only posts.
    image is optional (blank=True, null=True).
    """
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)  # Optional for text posts
    caption = models.TextField(max_length=2200, blank=True, default='')
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.username} at {self.created_at.strftime('%Y-%m-%d')}"

    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.comments.count()

    def is_text_only(self):
        return not bool(self.image)


class Comment(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=1000)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post.id}"


class Message(BaseModel):
    """
    Direct messages between users with like/reaction support.
    """
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(max_length=2000)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='liked_messages', blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"

    def like_count(self):
        return self.likes.count()


class Follow(BaseModel):
    """
    Follower/following relationship between users.
    follower → the user who is following
    following → the user being followed
    """
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_set')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_set')

    class Meta:
        unique_together = ('follower', 'following')  # Can't follow same person twice

    def __str__(self):
        return f"{self.follower.username} → {self.following.username}"
