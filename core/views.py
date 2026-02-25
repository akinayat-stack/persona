# core/views.py — Persona Social Media Application

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Post, Profile, Comment, Message, Follow
from .forms import PostForm, CommentForm, ProfileEditForm, RegisterForm, MessageForm


# ── 1. HOME / FEED ──────────────────────────────────────────────────────────────

@login_required
def home(request):
    """Feed: only posts from followed users (and self), newest-first."""
    # Get users the current user follows
    followed_users = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    # Include own posts
    user_ids = list(followed_users) + [request.user.id]
    posts = Post.objects.select_related('author', 'author__profile').prefetch_related('likes', 'comments').filter(author_id__in=user_ids).order_by('-created_at')
    return render(request, 'core/home.html', {'posts': posts, 'page_title': 'Feed'})


# ── 2. PROFILE ──────────────────────────────────────────────────────────────────
@login_required
def profile(request, username):
    viewed_user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(author=viewed_user).order_by('-created_at')
    is_own_profile = (request.user == viewed_user)

    # Follow stats
    followers_count = Follow.objects.filter(following=viewed_user).count()
    following_count = Follow.objects.filter(follower=viewed_user).count()
    is_following = False
    if not is_own_profile:
        is_following = Follow.objects.filter(follower=request.user, following=viewed_user).exists()

    form = None
    if is_own_profile:
        if request.method == 'POST' and 'save_profile' in request.POST:
            # FIX: Explicitly bind both POST data and FILES, save to DB
            form = ProfileEditForm(request.POST, request.FILES, instance=request.user.profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated!')
                return redirect('profile', username=request.user.username)
        else:
            form = ProfileEditForm(instance=request.user.profile)

    return render(request, 'core/profile.html', {
        'viewed_user': viewed_user,
        'user_posts': user_posts,
        'is_own_profile': is_own_profile,
        'form': form,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
        'page_title': f"{viewed_user.username}'s Profile",
    })


# ── 3. FOLLOW / UNFOLLOW ────────────────────────────────────────────────────────
@login_required
def follow_toggle(request, username):
    """Toggle follow/unfollow. Returns JSON for AJAX or redirects."""
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return redirect('profile', username=username)

    follow_obj = Follow.objects.filter(follower=request.user, following=target).first()
    if follow_obj:
        follow_obj.delete()
        following = False
    else:
        Follow.objects.create(follower=request.user, following=target)
        following = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'following': following,
            'followers_count': Follow.objects.filter(following=target).count(),
        })
    return redirect('profile', username=username)


# ── 4. CREATE POST ──────────────────────────────────────────────────────────────
@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Post shared!')
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'core/create_post.html', {'form': form, 'page_title': 'Create Post'})


# ── 5. POST DETAIL ──────────────────────────────────────────────────────────────
@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('author', 'author__profile'), id=post_id)
    comments = post.comments.select_related('author', 'author__profile').all()

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            c = comment_form.save(commit=False)
            c.post = post
            c.author = request.user
            c.save()
            return redirect('post_detail', post_id=post.id)
    else:
        comment_form = CommentForm()

    return render(request, 'core/post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'page_title': f"Post by {post.author.username}",
    })


# ── 6. LIKE POST ────────────────────────────────────────────────────────────────
@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'count': post.like_count()})
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ── 7. LIKE MESSAGE ─────────────────────────────────────────────────────────────
@login_required
def like_message(request, message_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    message = get_object_or_404(Message, id=message_id)
    if request.user not in [message.sender, message.receiver]:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    if request.user in message.likes.all():
        message.likes.remove(request.user)
        liked = False
    else:
        message.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'count': message.like_count()})


# ── 8. MESSENGER ────────────────────────────────────────────────────────────────
def _build_conversations(user):
    sent_to = Message.objects.filter(sender=user).values_list('receiver', flat=True).distinct()
    received_from = Message.objects.filter(receiver=user).values_list('sender', flat=True).distinct()
    partner_ids = set(list(sent_to) + list(received_from))
    partners = User.objects.filter(id__in=partner_ids).select_related('profile')
    convs = []
    for partner in partners:
        last_msg = Message.objects.filter(
            Q(sender=user, receiver=partner) | Q(sender=partner, receiver=user)
        ).order_by('-timestamp').first()
        unread = Message.objects.filter(sender=partner, receiver=user, is_read=False).count()
        convs.append({'partner': partner, 'last_message': last_msg, 'unread_count': unread})
    convs.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else 0, reverse=True)
    return convs


@login_required
def messenger(request):
    return render(request, 'core/messenger.html', {
        'conversations': _build_conversations(request.user),
        'page_title': 'Messages',
        'active_chat': None,
    })


@login_required
def chat(request, username):
    other_user = get_object_or_404(User, username=username)
    if other_user == request.user:
        return redirect('messenger')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = other_user
            msg.save()
            return redirect('chat', username=other_user.username)
    else:
        form = MessageForm()

    chat_messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp').prefetch_related('likes')

    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)

    return render(request, 'core/messenger.html', {
        'other_user': other_user,
        'chat_messages': chat_messages,
        'form': form,
        'conversations': _build_conversations(request.user),
        'active_chat': other_user,
        'page_title': f'Chat with {other_user.username}',
    })


# ── 9. USER SEARCH ──────────────────────────────────────────────────────────────
@login_required
def search_users(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = User.objects.filter(
            username__icontains=query
        ).exclude(id=request.user.id).select_related('profile')[:20]
    return render(request, 'core/search.html', {
        'query': query,
        'results': results,
        'page_title': 'Search People',
    })


# ── 10. AUTH ─────────────────────────────────────────────────────────────────────
def auth_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    login_error = None
    register_form = RegisterForm()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
            if user:
                login(request, user)
                return redirect('home')
            login_error = 'Invalid username or password.'
        elif action == 'register':
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                Profile.objects.get_or_create(user=user)
                login(request, user)
                return redirect('home')
    return render(request, 'core/auth.html', {
        'register_form': register_form,
        'login_error': login_error,
        'page_title': 'Sign In',
    })


def logout_view(request):
    logout(request)
    return redirect('auth')


# ── 11. DELETE POST ──────────────────────────────────────────────────────────────
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        if post.image:
            post.image.delete(save=False)
        post.delete()
        messages.success(request, 'Post deleted.')
    return redirect('profile', username=request.user.username)


# ── 12. EDIT POST ──────────────────────────────────────────────────────────────
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, 'core/edit_post.html', {'form': form})


# ── 13. DELETE COMMENT ─────────────────────────────────────────────────────────
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    post_id = comment.post.id
    comment.delete()
    return redirect('post_detail', post_id=post_id)
