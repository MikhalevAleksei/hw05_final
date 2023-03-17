from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Follow, Post

User = get_user_model()


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый пользователь')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='Привет!',
            author=cls.user,
            group=cls.group,
        )
        cls.templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'},
            ),
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def posts_check_all_fields(self, post):
        """Метод, проверяющий поля поста."""
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)

    def test_posts_pages_use_correct_template(self):
        """Проверка, использует ли адрес URL соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_context_index_template(self):
        """
        Проверка, сформирован ли шаблон group_list с
        правильным контекстом.

        Появляется ли пост, при создании на главной странице.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        self.posts_check_all_fields(response.context['page_obj'][0])
        last_post = response.context['page_obj'][0]
        self.assertEqual(last_post, self.post)

    def test_posts_context_group_list_template(self):
        """
        Проверка, сформирован ли шаблон group_list с
        правильным контекстом.

        Появляется ли пост, при создании на странице его группы.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ),
        )
        test_group = response.context['group']
        self.posts_check_all_fields(response.context['page_obj'][0])
        test_post = str(response.context['page_obj'][0])
        self.assertEqual(test_group, self.group)
        self.assertEqual(test_post, str(self.post))

    def test_posts_context_post_create_template(self):
        """
        Проверка, сформирован ли шаблон post_create с
        правильным контекстом.
        """
        response = self.authorized_client.get(reverse('posts:post_create'))

        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_posts_context_post_edit_template(self):
        """
        Проверка, сформирован ли шаблон post_edit с
        правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'pk': self.post.id},
            ),
        )

        form_fields = {'text': forms.fields.CharField}

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_posts_context_profile_template(self):
        """
        Проверка, сформирован ли шаблон profile с
        правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username},
            ),
        )
        profile = {'author': self.post.author}

        for value, expected in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

        self.posts_check_all_fields(response.context['page_obj'][0])
        test_page = response.context['page_obj'][0]
        self.assertEqual(test_page, self.user.posts.all()[0])

    def test_posts_context_post_detail_template(self):
        """
        Проверка, сформирован ли шаблон post_detail с
        правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            ),
        )

        profile = {'post': self.post}

        for value, expected in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, expected)

    def test_posts_not_from_foreign_group(self):
        """
        Проверка, при указании группы поста, попадает
        ли он в другую группу.
        """
        response = self.authorized_client.get(reverse('posts:index'))
        self.posts_check_all_fields(response.context['page_obj'][0])
        post = response.context['page_obj'][0]
        group = post.group
        self.assertEqual(group, self.group)


class PostsPaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый пользователь')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        for count in range(13):
            cls.post = Post.objects.create(
                text=f'Тестовый текст поста номер {count}',
                author=cls.user,
            )

    def test_posts_if_first_page_has_ten_records(self):
        """Проверка, содержит ли первая страница 10 записей."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page_obj').object_list), 10)

    def test_posts_if_second_page_has_three_records(self):
        """Проверка, содержит ли вторая страница 3 записи."""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page_obj').object_list), 3)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='user')
        cls.user_following = User.objects.create_user(username='user_1')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовый текст',
        )

    def setUp(self):
        self.following_client = Client()
        self.follower_client = Client()
        self.following_client.force_login(self.user_following)
        self.follower_client.force_login(self.user_follower)

    def test_follow(self):
        """Зарегистрированный пользователь может подписываться."""
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            args=(self.user_following.username,)))
        self.assertEqual(Follow.objects.count(), follower_count + 1)

    def test_unfollow(self):
        """Зарегистрированный пользователь может отписаться."""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            args=(self.user_following.username,)))
        self.assertEqual(Follow.objects.count(), follower_count - 1)

    def test_new_post_see_follower(self):
        """Пост появляется в ленте подписавшихся."""
        posts = Post.objects.create(
            text=self.post.text,
            author=self.user_following,
        )
        follow = Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, posts)
        follow.delete()
        response_2 = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response_2.context['page_obj']), 0)
