from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostsUrlsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='slug',
            description='Тестовое описание',
        )
        cls.author = User.objects.create_user(username='author_username')
        cls.no_author = User.objects.create_user(
            username='not_author_username',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

        cls.author_authorized_client = Client()
        cls.author_authorized_client.force_login(cls.author)

        cls.no_author_client = Client()
        cls.no_author_client.force_login(cls.no_author)

        cls.urls = {
            'group_list': reverse('posts:group_list',
                                  kwargs={'slug': cls.group.slug}),
            'index': reverse('posts:index'),
            'missing': 'not-exist-page-missing/',
            'profile': reverse('posts:profile',
                               kwargs={'username': cls.author.username}),
            'post_create': reverse('posts:post_create'),
            'post_detail': reverse('posts:post_detail', kwargs={
                'post_id': cls.post.id}),
            'post_edit': reverse('posts:post_edit', kwargs={
                'pk': cls.post.id}),
        }

    def test_http_statuses(self) -> None:
        httpstatuses = (
            (self.urls.get('group_list'), HTTPStatus.OK,
             self.author_authorized_client),
            (self.urls.get('index'), HTTPStatus.OK,
             self.author_authorized_client),
            (self.urls.get('missing'), HTTPStatus.NOT_FOUND,
             self.author_authorized_client),
            (self.urls.get('profile'), HTTPStatus.OK,
             self.author_authorized_client),
            (self.urls.get('post_create'), HTTPStatus.OK,
             self.author_authorized_client),
            (self.urls.get('post_detail'), HTTPStatus.OK,
             self.author_authorized_client),
            (self.urls.get('post_edit'), HTTPStatus.OK,
             self.author_authorized_client),

            (self.urls.get('post_edit'), HTTPStatus.FOUND,
             self.no_author_client),

            (self.urls.get('post_create'), HTTPStatus.FOUND, self.client),
            (self.urls.get('post_edit'), HTTPStatus.FOUND, self.client),

            (self.urls.get('group_list'), HTTPStatus.OK, self.client),
            (self.urls.get('index'), HTTPStatus.OK, self.client),
            (self.urls.get('missing'), HTTPStatus.NOT_FOUND, self.client),
            (self.urls.get('profile'), HTTPStatus.OK, self.client),
            (self.urls.get('post_detail'), HTTPStatus.OK, self.client),

        )
        for url, status_code, client in httpstatuses:
            with self.subTest():
                self.assertEqual(client.get(url).status_code, status_code)

    def test_templates(self) -> None:
        templates = (
            (self.urls.get('group_list'), 'posts/group_list.html',
             self.author_authorized_client),
            (self.urls.get('index'), 'posts/index.html',
             self.author_authorized_client),
            (self.urls.get('profile'), 'posts/profile.html',
             self.author_authorized_client),
            (self.urls.get('post_create'), 'posts/create_post.html',
             self.author_authorized_client),
            (self.urls.get('post_detail'), 'posts/post_detail.html',
             self.author_authorized_client),
            (self.urls.get('post_edit'), 'posts/create_post.html',
             self.author_authorized_client),

            (
                self.urls.get('group_list'), 'posts/group_list.html',
                self.client),
            (self.urls.get('index'), 'posts/index.html', self.client),
            (self.urls.get('profile'), 'posts/profile.html', self.client),
            (self.urls.get('post_detail'), 'posts/post_detail.html',
             self.client),
        )

        for url, template_name, client in templates:
            with self.subTest():
                self.assertTemplateUsed(client.get(url), template_name)

    def test_redirects(self) -> None:
        redirects = (

            (self.urls.get('post_edit'),
             reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
             self.no_author_client),

            (self.urls.get('post_create'),
             reverse('users:login') + '?next=' + reverse('posts:post_create'),
             self.client),
            (self.urls.get('post_edit'),
             reverse('users:login')
             + '?next='
             + reverse('posts:post_edit',
                       kwargs={
                           'pk': self.post.id}),
             self.client),

        )
        for url, redirect, client in redirects:
            with self.subTest():
                self.assertRedirects(client.get(url), redirect)

    def test_404_page(self):
        """Проверка 404 для несуществующих страниц."""
        url = '/unexisting_page/'
        clients = (
            self.authorized_client,
            self.authorized_client_no_author,
            self.client,
        )
        for role in clients:
            with self.subTest(url=url):
                response = role.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertTemplateUsed(response, 'core/404.html')
