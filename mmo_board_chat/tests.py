from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Post, Reply, Category
from .forms import RegisterForm, PostForm, ReplyForm

User = get_user_model()


class MMOBoardTests(TestCase):
    def setUp(self):
        """Настройка данных для каждого теста"""
        self.client = Client()

        # Создаём категорию
        self.category = Category.objects.create(name='mmo')  # 'mmo' должно быть в CATEGORIES

        # Создаём пользователя (автора)
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpassword123',
            email_confirmed=True
        )

        # Создаём второго пользователя (для откликов)
        self.other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='otherpassword123',
            email_confirmed=True
        )

        # Создаём тестовый пост
        self.post = Post.objects.create(
            title='Тестовое объявление',
            content='Описание',
            author=self.user,
            category=self.category
        )

    def test_register_user(self):
        """Тест: регистрация нового пользователя"""
        response = self.client.post(reverse('mmo_board_chat:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
        })
        # Должен быть редирект на страницу подтверждения
        self.assertEqual(response.status_code, 302)
        # Проверяем, что пользователь создан
        self.assertTrue(User.objects.filter(email='new@example.com').exists())
        # Проверяем, что email не подтверждён
        user = User.objects.get(email='new@example.com')
        self.assertFalse(user.email_confirmed)

    def test_create_post_authorized(self):
        """Тест: создание объявления авторизованным пользователем"""
        self.client.login(username='test@example.com', password='testpassword123')
        response = self.client.post(reverse('mmo_board_chat:post_create'), {
            'title': 'Новое объявление',
            'content': '<p>Текст нового объявления</p>',  # CKEditor ожидает HTML
            'category': self.category.id,
        })

        # Если форма невалидна, Django вернёт 200 и страницу с ошибками
        if response.status_code == 200:
            print("ОШИБКИ ФОРМЫ:", response.context['form'].errors)

        # Должен быть редирект на страницу поста
        self.assertEqual(response.status_code, 302)

        # Проверяем, что пост создан
        self.assertTrue(Post.objects.filter(title='Новое объявление').exists())
        new_post = Post.objects.get(title='Новое объявление')
        self.assertEqual(new_post.author, self.user)

    def test_create_post_unauthorized(self):
        """Тест: неавторизованный пользователь не может создать объявление"""
        response = self.client.get(reverse('mmo_board_chat:post_create'))
        # Должен быть редирект на логин (302)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_home_page(self):
        """Тест: главная страница отдаёт список объявлений"""
        response = self.client.get(reverse('mmo_board_chat:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовое объявление')
        # Проверяем, что используется правильный шаблон
        self.assertTemplateUsed(response, 'mmo_board_chat/home.html')

    def test_create_reply(self):
        """Тест: создание отклика на объявление"""
        self.client.login(username='other@example.com', password='otherpassword123')
        response = self.client.post(reverse('mmo_board_chat:post_detail', args=[self.post.id]), {
            'text': 'Мой отклик на объявление'
        })

        if response.status_code == 200:
            print("ОШИБКИ ФОРМЫ ОТКЛИКА:", response.context['form'].errors)

        # Должен быть редирект обратно на страницу поста
        self.assertEqual(response.status_code, 302)

        # Проверяем, что отклик создан
        self.assertTrue(Reply.objects.filter(text='Мой отклик на объявление').exists())
        reply = Reply.objects.get(text='Мой отклик на объявление')
        self.assertEqual(reply.author, self.other_user)
        self.assertEqual(reply.post, self.post)
        self.assertFalse(reply.is_accepted)

    def test_accept_reply_by_author(self):
        """Тест: автор объявления может принять отклик"""
        reply = Reply.objects.create(
            post=self.post,
            author=self.other_user,
            text='Отклик для принятия'
        )
        self.client.login(username='test@example.com', password='testpassword123')
        response = self.client.post(reverse('mmo_board_chat:reply_accept', args=[reply.id]))

        self.assertEqual(response.status_code, 302)
        reply.refresh_from_db()
        self.assertTrue(reply.is_accepted)



        print("Reply author:", reply.post.author, "Current user:", self.user)
        # Проверяем, что отклик принят
        reply.refresh_from_db()
        self.assertTrue(reply.is_accepted)

    def test_accept_reply_by_non_author(self):
        """Тест: не-автор не может принять отклик"""
        reply = Reply.objects.create(
            post=self.post,
            author=self.other_user,
            text='Отклик для принятия'
        )
        logged_in = self.client.login(username='other@example.com', password='otherpassword123')

        response = self.client.post(reverse('mmo_board_chat:reply_accept', args=[reply.id]))

        self.assertEqual(response.status_code, 403)
        reply.refresh_from_db()
        self.assertFalse(reply.is_accepted)