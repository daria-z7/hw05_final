import math
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from ..models import Group, Post, Follow

User = get_user_model()

page_count = settings.PER_PAGE_COUNT
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create_user(username='auth1')
        cls.user2 = User.objects.create_user(username='auth2')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='leo-hater',
            description='Тестовое описание',
        )
        cls.group1 = Group.objects.create(
            title='Тестовая группа1',
            slug='group1',
            description='Тестовое описание1',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста 1',
            group=PostPagesTests.group,
            image=uploaded,
        )

        cls.form = PostForm

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:posts_name',
                kwargs={'slug': PostPagesTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post.id}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.id}
            )
        )
        post = get_object_or_404(Post, pk=PostPagesTests.post.id)
        self.assertEqual(
            response.context.get('post').author.id,
            post.author.id
        )
        self.assertEqual(
            response.context.get('post').id,
            PostPagesTests.post.id
        )
        self.assertEqual(response.context.get('post').text, post.text)
        self.assertEqual(
            response.context.get('post').group.slug,
            post.group.slug
        )
        self.assertEqual(
            response.context.get('post').image,
            post.image
        )

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post.id}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_in_correct_pages(self):
        """Новый пост на правильных страницах."""
        post_text = 'Текст поста 16'
        form_group = PostPagesTests.group1
        form_data = {
            'text': post_text,
            'group': form_group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        posts_index = Post.objects.all()
        self.assertTrue(
            posts_index.filter(
                text=form_data['text'],
            ).exists()
        )
        group = get_object_or_404(Group, slug=form_group.slug)
        posts_group_list = group.post_set.all()
        self.assertTrue(
            posts_group_list.filter(
                text=form_data['text'],
            ).exists()
        )
        author = get_object_or_404(User, username=self.user)
        posts_profile = author.posts.all()
        self.assertTrue(
            posts_profile.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_new_post_not_in_incorrect_group(self):
        """Новый пост не попадает не в ту группу."""
        post_text = 'Текст поста 16'
        form_group = PostPagesTests.group1
        another_group = PostPagesTests.group
        form_data = {
            'text': post_text,
            'group': form_group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        group = get_object_or_404(Group, slug=another_group.slug)
        posts_group_list = group.post_set.all()
        self.assertFalse(
            posts_group_list.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_new_post_seen_by_followers(self):
        """Новый пост попадает в избранное подписчика."""
        Follow.objects.create(user=self.user1, author=self.user)
        post_text = 'Текст поста 16'
        form_group = PostPagesTests.group1
        form_data = {
            'text': post_text,
            'group': form_group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        following_posts_1 = Post.objects.filter(
            author__in=Follow.objects.filter(
                user=self.user1
            ).values_list('author_id')
        ).count()
        author_posts = Post.objects.filter(author=self.user).count()
        following_posts_2 = Post.objects.filter(
            author__in=Follow.objects.filter(
                user=self.user2
            ).values_list('author_id')
        ).count()
        self.assertEqual(following_posts_1, author_posts)
        self.assertNotEqual(following_posts_2, author_posts)

    def test_authorized_can_follow(self):
        """Авторизованный юзер может подписываться."""
        following_count_1 = Follow.objects.filter(
            user=self.user
        ).filter(author=self.user1).count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user1.username}
        ))
        following_count_2 = Follow.objects.filter(
            user=self.user
        ).filter(author=self.user1).count()
        self.assertEqual(following_count_1, following_count_2 - 1)

    def test_authorized_can_unfollow(self):
        """Авторизованный юзер может отписываться."""
        Follow.objects.create(user=self.user, author=self.user1)
        following_count_1 = Follow.objects.filter(
            user=self.user
        ).filter(author=self.user1).count()
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user1.username}
        ))
        following_count_2 = Follow.objects.filter(
            user=self.user
        ).filter(author=self.user1).count()
        self.assertEqual(following_count_1, 1)
        self.assertEqual(following_count_2, 0)

    def test_follow_yourself(self):
        """Юзер не может подписаться на себя."""
        following_count_1 = Follow.objects.filter(user=self.user).count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}
        ))
        following_count_2 = Follow.objects.filter(user=self.user).count()
        self.assertEqual(following_count_1, following_count_2)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user1 = User.objects.create_user(username='auth1')

        group_list = list()
        for i in range(1, 3):
            group_list.append(
                Group(
                    title=f'Тестовая группа {i}',
                    slug=f'group-slug-{i}',
                    description=f'Тестовое описание {i}',
                )
            )

        cls.group = Group.objects.bulk_create(group_list)
        group = get_object_or_404(Group, pk=Group.objects.earliest('id').id)
        group_2 = get_object_or_404(Group, pk=Group.objects.latest('id').id)

        post_list = list()
        for i in range(1, 13):
            post_list.append(
                Post(
                    author=cls.user,
                    text=f'Текст поста {i}',
                    group=group,
                )
            )

        cls.post = Post.objects.bulk_create(post_list)
        Post.objects.all()

        cls.post14 = Post.objects.create(
            author=cls.user1,
            text='Текст поста 14',
            group=group_2
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post15 = Post.objects.create(
            author=cls.user,
            text='Текст поста 15',
            image=uploaded,
            group=group,
        )

        cls.form = PostForm

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_index_page_contains_ten_records(self):
        """Пажинатор выводит 10 записей на главную."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), page_count)

    def test_index_second_page_contains_three_records(self):
        """Проверка отображения кол-ва постов на посл стр"""
        post_count = Post.objects.count()
        if post_count - page_count > 0:
            response = self.client.get(
                (reverse('posts:index')
                 + f'?page={math.ceil(post_count / page_count)}')
            )
            self.assertEqual(
                len(response.context['page_obj']),
                post_count - page_count
            )

    def test_group_list_page_contains_ten_records(self):
        """Пажинатор group_list выводит 10 записей на главную."""
        response = self.client.get(
            reverse(
                'posts:posts_name',
                kwargs={'slug': self.post[0].group.slug}
            ),
        )
        self.assertEqual(len(response.context['page_obj']), page_count)

    def test_group_list_second_page_contains_three_records(self):
        """Проверка отображения кол-ва постов на посл стр group_list"""
        post_count = Post.objects.filter(group=self.post[0].group).count()
        if post_count - page_count > 0:
            response = self.client.get(
                reverse(
                    'posts:posts_name',
                    kwargs={'slug': self.post[0].group.slug}
                ) + f'?page={math.ceil(post_count / page_count)}'
            )
            self.assertEqual(
                len(response.context['page_obj']),
                post_count - page_count
            )

    def test_profile_page_contains_ten_records(self):
        """Пажинатор profile выводит 10 записей на главную."""
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user}
            ),
        )
        self.assertEqual(len(response.context['page_obj']), page_count)

    def test_profile_second_page_contains_three_records(self):
        """На второй странице profile 3 поста"""
        post_count = Post.objects.filter(author=self.user).count()
        if post_count - page_count > 0:
            response = self.client.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.user}
                ) + '?page=2'
            )
            self.assertEqual(
                len(response.context['page_obj']),
                post_count - page_count
            )

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        post_count = Post.objects.count()
        k: int
        for i in range(math.ceil(post_count / page_count)):
            response = self.client.get(
                (reverse('posts:index')
                 + f'?page={i}')
            )
            k = 0
            for post in response.context['page_obj']:
                if post.image:
                    self.assertEqual(
                        post.image,
                        self.post15.image
                    )
                k += 1

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        post_count = Post.objects.filter(group=self.post[0].group).count()
        k: int
        for i in range(math.ceil(post_count / page_count)):
            response = self.client.get(
                reverse(
                    'posts:posts_name',
                    kwargs={'slug': self.post[0].group.slug}
                ) + f'?page={i}'
            )
            k = 0
            for post in response.context['page_obj']:
                if post.image:
                    self.assertEqual(
                        post.image,
                        self.post15.image
                    )
                k += 1

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        post_count = Post.objects.filter(author=self.user).count()
        k: int
        for i in range(math.ceil(post_count / page_count)):
            response = self.client.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.user}
                ) + f'?page={i}'
            )
            k = 0
            for post in response.context['page_obj']:
                if post.image:
                    self.assertEqual(
                        post.image,
                        self.post15.image
                    )
                k += 1
