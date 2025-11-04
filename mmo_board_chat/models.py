from django.db import models
from django.contrib.auth.models import AbstractUser
from ckeditor.fields import RichTextField

from mmo_board_chat.resources import CATEGORIES
import secrets


class User(AbstractUser):
    """
    КАСТОМНАЯ МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ
    """
    email = models.EmailField(unique=True)
    email_confirmed = models.BooleanField(default=False)
    confirmation_code = models.CharField(max_length=40, blank=True)
    username = models.CharField(max_length=30)

    USERNAME_FIELD = 'email' # Авторизация по email
    REQUIRED_FIELDS = ['username']

    def generate_confirmation_code(self):
        """
        Генерация уникального кода подтверждения для email
        Используется при регистрации
        """
        code = secrets.token_urlsafe(20)
        self.confirmation_code = code
        self.save()
        return code

    def __str__(self):
        return self.email

class Category(models.Model):
    """
    МОДЕЛЬ КАТЕГОРИЙ
    """
    name = models.CharField(max_length=6, choices=CATEGORIES, unique=True, )

    def __str__(self):
        return dict(CATEGORIES).get(self.name, self.name)

class Post(models.Model):
    """
    МОДЕЛЬ ОБЪЯВЛЕНИЙ
    """
    title = models.CharField('Заголовок', max_length=200)
    content = RichTextField('Содержание')
    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE, # При удалении пользователя удаляются его объявления
        verbose_name='Автор'
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.PROTECT, # Защита от удаления категории с существующими объявлениями
        verbose_name='Категория'
    )
    image = models.ImageField(
        'Изображение',
        upload_to='posts/', # Папка для загрузки изображений
        blank=True,
        null=True
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    def __str__(self):
        return self.title


class Reply(models.Model):
    """
    МОДЕЛЬ ОТКЛИКОВ
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name="Объявление")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    text = models.TextField("Текст отклика")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    is_accepted = models.BooleanField("Принят", default=False)

    def status_badge(self):
        """
        Вспомогательный метод для отображения статуса в HTML
        """
        if self.is_accepted:
            return '<span class="badge bg-success">Принят</span>'
        return ''

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Отклик"
        verbose_name_plural = "Отклики"

    def __str__(self):
        return f"Отклик от {self.author.username} на {self.post.title}"


