from django.test import Client, TestCase
from django.core.cache import cache
from http import HTTPStatus

from posts.models import Group, Post, User


class TestPostsURL(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.user1 = User.objects.create(username='TestUser1')
        cls.post = Post.objects.create(
            author=cls.user,
        )
        cls.group = Group.objects.create(
            slug='test-slug'
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = TestPostsURL.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user1 = TestPostsURL.user1
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)

    def test_urls_status_code_guest(self):
        template = {
            '/': HTTPStatus.OK,
            '/new/': HTTPStatus.FOUND,
            f'/group/{TestPostsURL.group.slug}/': HTTPStatus.OK,
            f'/{TestPostsURL.user}/': HTTPStatus.OK,
            f'/{TestPostsURL.user}/{TestPostsURL.post.id}/': HTTPStatus.OK,
            f'/{TestPostsURL.user}/{TestPostsURL.post.id}/edit/':
                HTTPStatus.FOUND
        }
        for adress, template in template.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, template)

    def test_urls_status_code_auth(self):
        template = {
            '/new/': HTTPStatus.OK,
            f'/group/{TestPostsURL.group.slug}/': HTTPStatus.OK,
            '/new/notexist/': HTTPStatus.NOT_FOUND,
            f'/{TestPostsURL.user}/': HTTPStatus.OK,
            f'/{TestPostsURL.user}/{TestPostsURL.post.id}/': HTTPStatus.OK,
            f'/{TestPostsURL.user}/{TestPostsURL.post.id}/edit/':
                HTTPStatus.OK,

        }
        for adress, template in template.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, template)

    def test_post_edit_auth_user_not_author(self):
        response = self.authorized_client1.get(
            f'/{TestPostsURL.user}/{TestPostsURL.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'index.html': '/',
            'new.html': '/new/',
            'post.html': f'/{TestPostsURL.user}/{TestPostsURL.post.id}/',
            'group.html': f'/group/{TestPostsURL.group.slug}/',
            'misc/404.html': '/new/notexist'
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_edit(self):
        response = self.authorized_client.get(
            f'/{TestPostsURL.user}/{TestPostsURL.post.id}/edit/')
        self.assertTemplateUsed(response, 'new.html')

    def test_redirect_from_edit_if_not_author(self):
        response = self.authorized_client1.get(
            f'/{TestPostsURL.user}/{TestPostsURL.post.id}/edit/')
        self.assertRedirects(
            response, f'/{TestPostsURL.user}/{TestPostsURL.post.id}/')
