from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from ..models import Group, Post

User = get_user_model()


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='leo-hater',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exists_at_desired_location(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{PostUrlTests.group.slug}/',
            'posts/profile.html': f'/profile/{self.user}/',
            'posts/post_detail.html': f'/posts/{int(PostUrlTests.post.id)}/',
        }

        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login_req_url_at_desired_loc(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
    
    def test_login_req_url_to_add_comment(self):
        post_id = PostUrlTests.post.id
        response = self.authorized_client.get(f'/posts/{int(post_id)}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_only_author_url_at_desired_loc(self):
        post_id = PostUrlTests.post.id
        response = self.authorized_client.get(f'/posts/{int(post_id)}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_non_exist_url(self):
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        pc_temp = 'posts/create_post.html'
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostUrlTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostUrlTests.user}/': 'posts/profile.html',
            f'/posts/{int(PostUrlTests.post.id)}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{int(PostUrlTests.post.id)}/edit/': pc_temp,
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
