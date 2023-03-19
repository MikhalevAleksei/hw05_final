import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.author = User.objects.create_user(username='Новый пользователь')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_posts_forms_create_post_auth(self):
        """Проверка, создает ли форма пост в базе,
         авторизованный пользователь."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_image.gif',
            content=small_gif,
            content_type='image/gif',
        )
        group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        form_data = {
            'text': 'Тестовый пост формы',
            'group': group.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), 1)
        post_to_check = Post.objects.first()

        self.assertEqual(form_data.get('text'), post_to_check.text)
        self.assertEqual(form_data.get('group'), post_to_check.group.id)
        self.assertEqual(f'posts/{form_data.get("image")}',
                         post_to_check.image)

    def test_posts_forms_edit_post_auth_author(self):
        """Проверка, редактируется ли пост
        Авторизованный пользователь."""

        post = Post.objects.create(
            author=self.author,
            text='Тестовый пост',
        )
        group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        form_data = {
            'text': 'Новый текст поста',
            'group': group.id,
        }
        self.authorized_client.post(reverse(
            'posts:post_edit',
            kwargs={'pk': post.id},
        ), data=form_data)
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id},
        ))
        self.assertEqual(response.context['post'].text, 'Новый текст поста')
        post_to_check = Post.objects.first()
        self.assertEqual(form_data.get('text'), post_to_check.text)
        self.assertEqual(form_data.get('group'), post_to_check.group.id)

    def test_posts_forms_create_post_not_auth(self):
        """Проверка, создает ли форма пост в базе,
         Не авторизованный пользователь."""

        form_data = {
            'text': 'Тестовый пост формы',
        }
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), 0)
        self.assertFalse(Post.objects.filter(
            text='Тестовый пост формы',
        ).exists())

    def test_posts_forms_edit_post_not_auth(self):
        """Проверка, редактируется ли пост
        Не авторизованный пользователь"""
        post = Post.objects.create(
            author=self.author,
            text='Тестовый пост',
        )
        form_data = {
            'text': 'Новый текст поста',
        }
        self.client.post(reverse(
            'posts:post_edit',
            kwargs={'pk': post.id},
        ), data=form_data)
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id},
        ))
        self.assertNotEqual(response.context['post'].text, 'Новый текст поста')
        self.assertFalse(Post.objects.filter(
            text='Новый текст поста',
        ).exists())

    def test_posts_forms_edit_post_auth_not_author(self):
        """Проверка, редактируется ли пост
        Авторизованный не автор"""
        post = Post.objects.create(
            author=self.author,
            text='Тестовый пост',
        )
        not_author = User.objects.create_user(username='not_author')

        authorized_client_not_author = Client()
        authorized_client_not_author.force_login(not_author)

        form_data = {
            'text': 'Новый текст поста',
        }
        self.client.post(reverse(
            'posts:post_edit',
            kwargs={'pk': post.id},
        ), data=form_data)
        response = authorized_client_not_author.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id},
        ))
        self.assertNotEqual(response.context['post'].text, 'Новый текст поста')
        self.assertFalse(Post.objects.filter(
            text='Новый текст поста',
        ).exists())

    def test_comment(self):
        """Проверка создания пользователем комментария"""
        post = Post.objects.create(
            text='Привет!',
            author=self.author,
        )
        comments_count = Comment.objects.count()
        form_data = {
            'post': post,
            'author': self.author,
            'text': 'text',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(post.id,)))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text='text',
            author=self.author).exists())
