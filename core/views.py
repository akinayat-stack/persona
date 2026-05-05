# core/views.py — Persona Social Media Application

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.apps import apps
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.forms import modelform_factory
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Count
import json
from .models import Post, Profile, Comment, Message, Follow
from .services import fetch_daily_quote
from .forms import (
    PostForm,
    CommentForm,
    ProfileEditForm,
    RegisterForm,
    LoginForm,
    MessageForm,
    AdminUserForm,
    AdminPostForm,
    AdminCommentForm,
)




def _get_page_size(request, setting_name: str, default: int, max_size: int = 50):
    configured = getattr(settings, setting_name, default)
    raw = request.GET.get('page_size', configured)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, min(value, max_size))
# ── 1. HOME / FEED ──────────────────────────────────────────────────────────────

@login_required
def home(request):
    """Feed: only posts from followed users (and self), newest-first."""
    # Get users the current user follows
    followed_users = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    # Include own posts
    user_ids = list(followed_users) + [request.user.id]
    posts = Post.objects.select_related('author', 'author__profile').prefetch_related('likes', 'comments').filter(author_id__in=user_ids).order_by('-created_at')
    page_size = _get_page_size(request, 'FEED_PAGE_SIZE', 10)
    paginator = Paginator(posts, page_size)
    page_obj = paginator.get_page(request.GET.get('page'))
    quote = fetch_daily_quote()
    return render(request, 'core/home.html', {
        'posts': page_obj,
        'page_obj': page_obj,
        'page_title': 'Feed',
        'daily_quote': quote,
        'quote_loading': False,
    })


# ── 2. PROFILE ──────────────────────────────────────────────────────────────────
@login_required
def profile(request, username):
    viewed_user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(author=viewed_user).order_by('-created_at')
    paginator = Paginator(user_posts, _get_page_size(request, 'PROFILE_PAGE_SIZE', 9))
    page_obj = paginator.get_page(request.GET.get('page'))
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
        'user_posts': page_obj,
        'page_obj': page_obj,
        'post_count': user_posts.count(),
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

    next_url = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
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
            messages.success(request, 'Comment added.')
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
            messages.success(request, 'Message sent.')
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
    results = User.objects.none()
    if query:
        results = User.objects.filter(
            username__icontains=query
        ).exclude(id=request.user.id).select_related('profile')
    paginator = Paginator(results, _get_page_size(request, 'SEARCH_PAGE_SIZE', 10))
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/search.html', {
        'query': query,
        'results': page_obj,
        'page_obj': page_obj,
        'total_results': paginator.count,
        'page_title': 'Search People',
    })


@login_required
def suggested_users(request):
    query = request.GET.get('q', '').strip()
    followed_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)

    users = User.objects.exclude(id=request.user.id).exclude(id__in=followed_ids).select_related('profile').annotate(post_count=Count('posts')).order_by('-date_joined')
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(profile__bio__icontains=query)
        )

    paginator = Paginator(users, _get_page_size(request, 'SUGGESTED_PAGE_SIZE', 12))
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/suggested_users.html', {
        'users': page_obj,
        'query': query,
        'result_count': paginator.count,
        'page_obj': page_obj,
        'page_title': 'Discover People',
    })


# ── 10. AUTH ─────────────────────────────────────────────────────────────────────
def auth_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    login_form = LoginForm(request=request)
    register_form = RegisterForm()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            login_form = LoginForm(request=request, data=request.POST)
            if login_form.is_valid():
                login(request, login_form.get_user())
                messages.success(request, 'Welcome back!')
                return redirect('home')
        elif action == 'register':
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                Profile.objects.get_or_create(user=user)
                login(request, user)
                messages.success(request, 'Registration successful. Welcome to Persona!')
                return redirect('home')
    return render(request, 'core/auth.html', {
        'login_form': login_form,
        'register_form': register_form,
        'page_title': 'Sign In',
    })


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
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
            messages.success(request, 'Post updated.')
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
    messages.success(request, 'Comment deleted.')
    return redirect('post_detail', post_id=post_id)


def _is_admin(user):
    return user.is_authenticated and user.is_staff


def _admin_only(request):
    if not _is_admin(request.user):
        return JsonResponse({'error': 'Admin access required.'}, status=403)
    return None


def _parse_json_body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode('utf-8'))


def _serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
    }


def _serialize_post(post):
    return {
        'id': post.id,
        'author_id': post.author_id,
        'author': post.author.username,
        'caption': post.caption,
        'created_at': post.created_at.isoformat(),
    }


def _serialize_comment(comment):
    return {
        'id': comment.id,
        'post_id': comment.post_id,
        'post': f'Post #{comment.post_id}',
        'author_id': comment.author_id,
        'author': comment.author.username,
        'content': comment.content,
        'created_at': comment.created_at.isoformat(),
    }


def _serialize_dynamic_review(review):
    payload = {'id': review.id}
    for field in review._meta.fields:
        if field.name == 'id':
            continue
        value = getattr(review, field.name)
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        elif hasattr(value, 'pk'):
            value = value.pk
        payload[field.name] = value
    return payload


def _get_review_model():
    for model in apps.get_models():
        if model._meta.model_name == 'review':
            return model
    return None


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')
    return render(
        request,
        'core/admin_dashboard.html',
        {
            'page_title': 'Admin Dashboard',
            'has_reviews': _get_review_model() is not None,
        },
    )


@login_required
@require_http_methods(['GET', 'POST'])
def admin_entity_collection(request, entity):
    unauthorized = _admin_only(request)
    if unauthorized:
        return unauthorized

    q = request.GET.get('q', '').strip()
    if entity == 'users':
        queryset = User.objects.all().order_by('id')
        if q:
            queryset = queryset.filter(Q(username__icontains=q) | Q(email__icontains=q))
        if request.method == 'POST':
            data = _parse_json_body(request)
            form = AdminUserForm(data)
            if form.is_valid():
                user = form.save()
                return JsonResponse({'item': _serialize_user(user)}, status=201)
            return JsonResponse({'errors': form.errors}, status=400)
        return JsonResponse({'items': [_serialize_user(item) for item in queryset[:200]]})

    if entity == 'posts':
        queryset = Post.objects.select_related('author').all().order_by('-created_at')
        if q:
            queryset = queryset.filter(Q(caption__icontains=q) | Q(author__username__icontains=q))
        if request.method == 'POST':
            data = _parse_json_body(request)
            form = AdminPostForm(data)
            if form.is_valid():
                post = form.save()
                return JsonResponse({'item': _serialize_post(post)}, status=201)
            return JsonResponse({'errors': form.errors}, status=400)
        return JsonResponse({'items': [_serialize_post(item) for item in queryset[:200]]})

    if entity == 'comments':
        queryset = Comment.objects.select_related('author', 'post').all().order_by('-created_at')
        if q:
            queryset = queryset.filter(
                Q(content__icontains=q)
                | Q(author__username__icontains=q)
                | Q(post__caption__icontains=q)
            )
        if request.method == 'POST':
            data = _parse_json_body(request)
            form = AdminCommentForm(data)
            if form.is_valid():
                comment = form.save()
                return JsonResponse({'item': _serialize_comment(comment)}, status=201)
            return JsonResponse({'errors': form.errors}, status=400)
        return JsonResponse({'items': [_serialize_comment(item) for item in queryset[:200]]})

    if entity == 'reviews':
        review_model = _get_review_model()
        if review_model is None:
            return JsonResponse({'error': 'Review model not found.'}, status=404)
        queryset = review_model.objects.all().order_by('-id')
        if q:
            query_fields = [field.name for field in review_model._meta.fields if getattr(field, 'get_internal_type', lambda: '')() in ['CharField', 'TextField', 'EmailField']]
            if query_fields:
                text_filter = Q()
                for field_name in query_fields:
                    text_filter |= Q(**{f'{field_name}__icontains': q})
                queryset = queryset.filter(text_filter)
        if request.method == 'POST':
            data = _parse_json_body(request)
            form_class = modelform_factory(review_model, exclude=[])
            form = form_class(data)
            if form.is_valid():
                obj = form.save()
                return JsonResponse({'item': _serialize_dynamic_review(obj)}, status=201)
            return JsonResponse({'errors': form.errors}, status=400)
        return JsonResponse({'items': [_serialize_dynamic_review(item) for item in queryset[:200]]})

    return JsonResponse({'error': 'Unsupported entity.'}, status=404)


@login_required
@require_http_methods(['PUT', 'PATCH', 'DELETE'])
def admin_entity_detail(request, entity, obj_id):
    unauthorized = _admin_only(request)
    if unauthorized:
        return unauthorized

    if entity == 'users':
        instance = get_object_or_404(User, id=obj_id)
        if request.method == 'DELETE':
            instance.delete()
            return JsonResponse({'ok': True})
        data = _parse_json_body(request)
        form = AdminUserForm(data, instance=instance)
        if form.is_valid():
            user = form.save()
            return JsonResponse({'item': _serialize_user(user)})
        return JsonResponse({'errors': form.errors}, status=400)

    if entity == 'posts':
        instance = get_object_or_404(Post, id=obj_id)
        if request.method == 'DELETE':
            instance.delete()
            return JsonResponse({'ok': True})
        data = _parse_json_body(request)
        form = AdminPostForm(data, instance=instance)
        if form.is_valid():
            post = form.save()
            return JsonResponse({'item': _serialize_post(post)})
        return JsonResponse({'errors': form.errors}, status=400)

    if entity == 'comments':
        instance = get_object_or_404(Comment, id=obj_id)
        if request.method == 'DELETE':
            instance.delete()
            return JsonResponse({'ok': True})
        data = _parse_json_body(request)
        form = AdminCommentForm(data, instance=instance)
        if form.is_valid():
            comment = form.save()
            return JsonResponse({'item': _serialize_comment(comment)})
        return JsonResponse({'errors': form.errors}, status=400)

    if entity == 'reviews':
        review_model = _get_review_model()
        if review_model is None:
            return JsonResponse({'error': 'Review model not found.'}, status=404)
        instance = get_object_or_404(review_model, id=obj_id)
        if request.method == 'DELETE':
            instance.delete()
            return JsonResponse({'ok': True})
        data = _parse_json_body(request)
        for field in instance._meta.fields:
            if field.name == 'id':
                continue
            if field.name in data:
                setattr(instance, field.name, data[field.name])
        try:
            instance.full_clean()
        except ValidationError as exc:
            return JsonResponse({'errors': exc.message_dict}, status=400)
        instance.save()
        return JsonResponse({'item': _serialize_dynamic_review(instance)})

    return JsonResponse({'error': 'Unsupported entity.'}, status=404)


@login_required
@require_http_methods(['GET'])
def admin_stats(request):
    unauthorized = _admin_only(request)
    if unauthorized:
        return unauthorized

    payload = {
        'users': User.objects.count(),
        'posts': Post.objects.count(),
        'comments': Comment.objects.count(),
    }
    review_model = _get_review_model()
    if review_model is not None:
        payload['reviews'] = review_model.objects.count()
    return JsonResponse(payload)
