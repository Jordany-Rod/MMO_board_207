from django.urls import path
from . import views
from django.conf import settings
from ckeditor_uploader import views as ckeditor_views
from django.views.decorators.csrf import csrf_exempt

app_name = 'mmo_board_chat'  # Пространство имен приложения

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),

    # Авторизация
    path('register/', views.register_view, name='register'),
    path('confirm/<str:code>/', views.confirm_email, name='confirm_email'),
    path('confirm/', views.confirm_email_manual, name='confirm_email_manual'),
    path('resend-code/', views.resend_code, name='resend_code'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('replies/<int:reply_id>/accept/', views.reply_accept, name='reply_accept'),
    path('replies/<int:reply_id>/delete/', views.reply_delete, name='reply_delete'),

    # Личный кабинет
    path('profile/', views.profile, name='profile'),

    # Работа с объявлениями
    path('posts/create/', views.create_post, name='post_create'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/<int:post_id>/reply/', views.create_reply, name='reply_create'),

    # API-эндпоинты (если будут нужны)
    path('api/posts/', views.api_posts, name='api_posts'),

    path('upload/', csrf_exempt(ckeditor_views.upload)),
    path('browse/', csrf_exempt(ckeditor_views.browse)),
]
