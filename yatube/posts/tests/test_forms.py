from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post


User = get_user_model()


class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Новый пользователь')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)


    def test_posts_forms_create_post_auth(self):
        """Проверка, создает ли форма пост в базе,
         авторизованный пользователь."""
        group = Group.objects.create(
            title='Тестовое название группы',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        form_data = {
            'text': 'Тестовый пост формы',
            'group': group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        self.assertEqual(Post.objects.count(), 1)
        post_to_check = Post.objects.first()

        self.assertEqual(form_data.get('text'), post_to_check.text)
        self.assertEqual(form_data.get('group'), post_to_check.group.id)


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
            author=self.author, ).exists())

