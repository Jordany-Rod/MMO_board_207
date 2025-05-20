from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponseForbidden, JsonResponse
from django.conf import settings
import random
import string

from .forms import RegisterForm, PostForm, ReplyForm
from .models import Post, Reply, Category, User



# Вспомогательные функции

def generate_confirmation_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))

def send_confirmation_email(user, code):
    subject = 'Подтверждение регистрации'
    message = f'''Здравствуйте, {user.username}!

Ваш код подтверждения: {code}

Или перейдите по прямой ссылке для подтверждения:
{settings.SITE_URL}/confirm/{code}/

Спасибо за регистрацию!'''

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

"""Главная страница со списком объявлений"""
def home(request):
    posts = Post.objects.all().order_by('-created_at')  # Сортировка по дате
    return render(request, 'mmo_board_chat/home.html', {'posts': posts})

# Аутентификация

"""Обработка входа пользователя"""
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Пожалуйста, заполните все поля')
            return redirect('mmo_board_chat:login')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'mmo_board_chat:profile'
            return redirect(next_url)
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')

    next_url = request.GET.get('next', '')
    return render(request, 'mmo_board_chat/login.html', {'next': next_url})

"""Обработка регистрации нового пользователя"""
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_confirmation_email(user, user.confirmation_code)
            messages.success(request, 'Проверьте email для подтверждения')
            return redirect('mmo_board_chat:confirm_email_manual')
    else:
        form = RegisterForm()

    return render(request, 'mmo_board_chat/register.html', {'form': form})


"""Автоподтверждение email по ссылке"""
def confirm_email(request, code):
    try:
        user = User.objects.get(confirmation_code=code)
        user.email_confirmed = True
        user.confirmation_code = ''
        user.save()
        login(request, user)
        messages.success(request, 'Email подтвержден!')
        return redirect('mmo_board_chat:profile')
    except User.DoesNotExist:
        messages.error(request, 'Неверный код')
        return redirect('mmo_board_chat:home')

"""Ручной ввод кода подтверждения"""
def confirm_email_manual(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        if not code:
            messages.error(request, 'Пожалуйста, введите код подтверждения')
            return render(request, 'mmo_board_chat/confirm_email.html')

        try:
            # Ищем пользователя с таким кодом подтверждения
            user = User.objects.get(confirmation_code=code)

            # Подтверждаем email
            user.email_confirmed = True
            user.confirmation_code = ''  # Удаляем использованный код
            user.save()

            # Авторизуем пользователя
            login(request, user)

            messages.success(request, 'Email успешно подтвержден!')
            return redirect('mmo_board_chat:profile')

        except User.DoesNotExist:
            messages.error(request, 'Неверный код подтверждения')
            return render(request, 'mmo_board_chat/confirm_email.html')

    # GET-запрос - просто отображаем форму
    return render(request, 'mmo_board_chat/confirm_email.html')

"""Повторная отправка кода подтверждения"""
def resend_code(request):
    if request.user.is_authenticated and not request.user.email_confirmed:
        code = request.user.generate_confirmation_code()

        # Отправка письма (используйте вашу функцию отправки)
        send_confirmation_email(request.user, code)

        messages.success(request, 'Новый код подтверждения отправлен на ваш email')
    else:
        messages.error(request, 'Не удалось отправить код')

    return redirect('mmo_board_chat:confirm_email_manual')

"""Выход из системы"""
def logout_view(request):
    logout(request)
    return redirect('mmo_board_chat:home')

# Работа с объявлениями

"""Создание нового объявления"""
@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('mmo_board_chat:post_detail', post_id=post.id)
    else:
        form = PostForm()

    return render(request, 'mmo_board_chat/post_form.html', {
        'form': form,
        'title': 'Создание объявления'
    })

"""Просмотр деталей объявления с откликами"""
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    replies = Reply.objects.filter(post=post).order_by('-created_at')

    if request.method == 'POST' and request.user.is_authenticated:
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.author = request.user
            reply.post = post
            reply.save()

            # Отправка уведомления автору поста
            send_mail(
                subject=f'Новый отклик на ваше объявление "{post.title}"',
                message=f'Пользователь {request.user.username} оставил отклик:\n\n{reply.text}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[post.author.email],
                fail_silently=True,
            )

            messages.success(request, 'Ваш отклик успешно отправлен!')
            return redirect('mmo_board_chat:post_detail', post_id=post.id)
    else:
        form = ReplyForm()

    return render(request, 'mmo_board_chat/post_detail.html', {
        'post': post,
        'replies': replies,
        'form': form,
    })

# Работа с откликами

@login_required
def profile(request):
    # Получаем все отклики на объявления пользователя
    replies = Reply.objects.filter(post__author=request.user).order_by('-created_at')

    # Фильтрация по статусу (принятые/непринятые)
    status_filter = request.GET.get('status')
    if status_filter == 'accepted':
        replies = replies.filter(is_accepted=True)
    elif status_filter == 'pending':
        replies = replies.filter(is_accepted=False)

    # Фильтрация по конкретному объявлению
    post_filter = request.GET.get('post')
    if post_filter:
        replies = replies.filter(post_id=post_filter)

    # Получаем все объявления пользователя для фильтра
    user_posts = Post.objects.filter(author=request.user)

    context = {
        'user_posts': user_posts,
        'replies': replies,
        'current_status': status_filter,
        'current_post': post_filter,
    }
    return render(request, 'mmo_board_chat/profile.html', context)

"""Принятие отклика на объявление"""
@login_required
def reply_accept(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)

    # Проверяем, что текущий пользователь - автор объявления
    if request.user != reply.post.author:
        return HttpResponseForbidden()

    reply.is_accepted = True
    reply.save()

    messages.success(request, f'Отклик от {reply.author.username} принят!')
    return redirect('mmo_board_chat:profile')

"""Удаление отклика"""
@login_required
def reply_delete(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)

    # Проверяем, что пользователь - автор объявления или автор отклика
    if request.user not in [reply.post.author, reply.author]:
        return HttpResponseForbidden()

    reply.delete()
    messages.success(request, 'Отклик удалён.')
    return redirect('mmo_board_chat:profile')


"""Удаление отклика"""
@login_required
def delete_reply(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)
    post_id = reply.post.id

    if request.user not in [reply.post.author, reply.author]:
        return HttpResponseForbidden()

    reply.delete()
    messages.success(request, 'Отклик удалён.')
    return redirect('mmo_board_chat:post_detail', post_id=post_id)

"""Создание отклика"""
@login_required
def create_reply(request, post_id):
    return redirect('post_detail', post_id=post_id)

# API-эндпоинт (пример)
def api_posts(request):
    return JsonResponse({'posts': []})  # Заглушка для API










