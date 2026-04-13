# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.auth_page, name='auth'),
    path('logout/', views.logout_view, name='logout'),

    # Main Pages
    path('feed/', views.home, name='home'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),

    # Post edit
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),

    # Comment delete
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),

    # Profile
    path('profile/<str:username>/', views.profile, name='profile'),

    # Search
    path('search/', views.search_users, name='search'),
    path('suggested/', views.suggested_users, name='suggested_users'),

    # Follow system
    path('follow/<str:username>/', views.follow_toggle, name='follow_toggle'),

    # Messenger
    path('messages/', views.messenger, name='messenger'),
    path('messages/<str:username>/', views.chat, name='chat'),

    # Message like (AJAX)
    path('messages/like/<int:message_id>/', views.like_message, name='like_message'),

    # Custom admin dashboard + admin API
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/api/stats/', views.admin_stats, name='admin_stats'),
    path('admin/api/<str:entity>/', views.admin_entity_collection, name='admin_entity_collection'),
    path('admin/api/<str:entity>/<int:obj_id>/', views.admin_entity_detail, name='admin_entity_detail'),
]
