from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

User = get_user_model()


class GroupModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='Тестовая группа')

    def test_group_str_title(self):
        """Проверка, совпадает ли название группы."""
        group = GroupModelsTest.group
        self.assertEqual(str(group), group.title)

    def test_group_verbose_name(self):
        """Проверка, совпадают ли verbose_name в полях Group."""
        group = GroupModelsTest.group
        field_verboses = {
            'title': 'Название сообщества',
            'description': 'Описание сообщества',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected,
                )


class PostModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый пользователь')
        cls.group = Group.objects.create(title='Тестовая группа')
        cls.post = Post.objects.create(
            text='Тестовый пост Тестовый пост Тест',
            author=cls.user,
            group=cls.group,
        )

    def test_post_str_text(self):
        """Проверка, выводятся ли только первые пятнадцать символов поста."""
        post = PostModelsTest.post
        text = post.text
        self.assertEqual(str(post), text[:15])

    def test_post_verbose_name(self):
        """Проверка, совпадают ли verbose_name в полях Post."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Post._meta.get_field(value).verbose_name, expected,
                )
