from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def test_Post_model_has_correct_object_name(self):
        text = PostModelTest.post
        expected_value = text.text
        self.assertEqual(expected_value, str(text)[:15])

    def test_Group_model_has_correct_object_name(self):
        text = PostModelTest.group
        expected_value = text.slug
        self.assertEqual(expected_value, str(text))
