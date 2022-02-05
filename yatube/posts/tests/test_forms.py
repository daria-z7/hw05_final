import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache

from posts.forms import PostForm, CommentForm
from ..models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ex_username = 'auth'
        ex_group_title = 'Тестовая группа'
        ex_group_slug = 'leo-hater'
        ex_description = 'Тестовое описание'
        ex_post_text = 'Старый тест'
        cls.user = User.objects.create_user(username=ex_username)
        cls.group = Group.objects.create(
            title=ex_group_title,
            slug=ex_group_slug,
            description=ex_description,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=ex_post_text,
            group=PostCreateFormTests.group
        )

        cls.form = PostForm
        cls.form1 = CommentForm

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post_create(self):
        """Создаётся новая запись в базе данных."""
        post_count = Post.objects.count()
        post_text = 'Текст поста'
        form_data = {
            'text': post_text,
            'group': PostCreateFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                pk=Post.objects.latest('id').id,
                group=form_data['group'],
                text=form_data['text'],
            ).exists()
        )

    def test_edit_post(self):
        """Редактируется запись в базе данных."""
        post_count = Post.objects.count()
        post_text = 'Новый текст'
        form_data = {
            'text': post_text,
            'group': PostCreateFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        post_id = PostCreateFormTests.post.id
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post_id})
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                pk=PostCreateFormTests.post.id,
                group=form_data['group'],
                text=form_data['text'],
            ).exists()
        )

    def test_new_comment_add(self):
        """Новый комментарий добавлен в базе данных."""
        comment_count = Comment.objects.count()
        comment_text = 'Текст комментария'
        form_data = {
            'text': comment_text,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=form_data,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostCreateFormTests.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                pk=Comment.objects.latest('id').id,
                text=form_data['text'],
            ).exists()
        )

    def test_cache_index_page(self):
        """Проверка работы кеша главной страницы."""
        response = self.client.get(reverse('posts:index'))
        data_before_clean = response
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        data_after_clean = response
        self.assertNotEqual(data_before_clean, data_after_clean)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormImageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ex_username = 'auth'
        ex_group_title = 'Тестовая группа'
        ex_group_slug = 'leo-hater'
        ex_description = 'Тестовое описание'
        ex_post_text = 'Старый тест'
        cls.user = User.objects.create_user(username=ex_username)
        cls.group = Group.objects.create(
            title=ex_group_title,
            slug=ex_group_slug,
            description=ex_description,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=ex_post_text,
            group=PostCreateFormImageTests.group
        )

        cls.form = PostForm

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_with_image(self):
        """Пост с картинкой добавлен."""
        posts_count = Post.objects.count()
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
        post_text = 'Текст поста с картинкой'
        form_data = {
            'text': post_text,
            'group': PostCreateFormImageTests.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                pk=Post.objects.latest('id').id,
                group=form_data['group'],
                text=form_data['text'],
                image='posts/small.gif',
            ).exists()
        )
