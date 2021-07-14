import shutil
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import request
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache
from http import HTTPStatus


from posts.forms import PostForm
from posts.models import Group, Post, User, Follow

User = get_user_model()


class TestViewPosts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create(username='TestUser')
        cls.user1 = User.objects.create(username='TestUser1')
        cls.user2 = User.objects.create(username='TestUser2')
        cls.group = Group.objects.create(slug='test-slug')
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = TestViewPosts.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user1 = TestViewPosts.user1
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        self.user2 = TestViewPosts.user2
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_pages_uses_correct_template(self):
        templates_page_names = {
            'index.html': reverse('index'),
            'group.html': reverse(
                'group_posts', kwargs={'slug': TestViewPosts.group.slug}
            ),
            'new.html': reverse('new_post'),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_context(self):
        content = {
            self.guest_client.get(reverse('index')).
            context['page'][0]: TestViewPosts.post,

            self.guest_client.get(reverse(
                'group_posts',
                kwargs={'slug': f'{TestViewPosts.group.slug}'})).
            context['page'][0]: TestViewPosts.post,

            self.guest_client.get(reverse(
                'group_posts', kwargs={'slug': TestViewPosts.group.slug})).
            context['group']: TestViewPosts.group,

            self.authorized_client.get(reverse('new_post')).
            context['form'].__class__: TestViewPosts.form.__class__,

            self.authorized_client.get(reverse('new_post')).
            context['title']: 'Новая запись',

            self.authorized_client.get(reverse('new_post')).
            context['header']: 'Добавить запись',

            self.authorized_client.get(reverse('new_post')).
            context['button']: 'Добавить',

            self.authorized_client.get(reverse(
                'post_edit', kwargs={'username': TestViewPosts.user,
                                     'post_id': TestViewPosts.post.id})).
            context['form'].__class__: TestViewPosts.form.__class__,

            self.authorized_client.get(reverse(
                'post_edit', kwargs={'username': TestViewPosts.user,
                                     'post_id': TestViewPosts.post.id})).
            context['title']: 'Редактировать запись',

            self.authorized_client.get(reverse(
                'post_edit', kwargs={'username': TestViewPosts.user,
                                     'post_id': TestViewPosts.post.id})).
            context['header']: 'Редактировать',

            self.authorized_client.get(reverse(
                'post_edit', kwargs={'username': TestViewPosts.user,
                                     'post_id': TestViewPosts.post.id})).
            context['button']: 'Сохранить',

            self.authorized_client.get(reverse(
                'profile', kwargs={'username': TestViewPosts.user})).
            context['page'][0]: TestViewPosts.post,

            self.authorized_client.get(reverse(
                'profile', kwargs={'username': TestViewPosts.user})).
            context['post_user_count']: TestViewPosts.user.posts.all().count(),

            self.authorized_client.get(reverse(
                'profile', kwargs={'username': TestViewPosts.user})).
            context['author']: TestViewPosts.user,

            self.authorized_client.get(reverse(
                'post', kwargs={'username': TestViewPosts.user,
                                'post_id': TestViewPosts.post.id})).
            context['post_user_count']: TestViewPosts.user.posts.all().count(),

            self.authorized_client.get(reverse(
                'post', kwargs={'username': TestViewPosts.user,
                                'post_id': TestViewPosts.post.id})).
            context['post']: TestViewPosts.post,
        }
        for reverse_name, context in content.items():
            with self.subTest(context=context):
                self.assertEqual(reverse_name, context)

    def test_shows_currect_image_context(self):
        context = {
            self.authorized_client.get(
                reverse('index')
            ).context['page'][0].image: f'{TestViewPosts.post.image}',

            self.authorized_client.get(
                reverse('profile', kwargs={'username': TestViewPosts.user})
            ).context['page'][0].image: TestViewPosts.post.image,

            self.authorized_client.get(
                reverse('group_posts', kwargs={
                    'slug': TestViewPosts.group.slug})
            ).context['page'][0].image: TestViewPosts.post.image,

            self.authorized_client.get(
                reverse('post', kwargs={'username': TestViewPosts.user,
                                        'post_id': TestViewPosts.post.id})
            ).context['post'].image: TestViewPosts.post.image
        }
        for reverse_name, template in context.items():
            with self.subTest(template=template):
                self.assertEqual(reverse_name, template)

    def test_cache_for_index_page(self):
        Post.objects.create(author=TestViewPosts.user, text='text')
        response_before = self.guest_client.get(reverse('index')).content
        Post.objects.create(author=TestViewPosts.user, text='test')
        response_after = self.guest_client.get(reverse('index')).content
        self.assertEqual(response_before, response_after)

    def test_user_can_follow_unfollow(self):
        self.authorized_client.get(
            reverse('profile_follow', kwargs={'username': TestViewPosts.user1})
        )
        self.assertTrue(Follow.objects.filter(user=TestViewPosts.user,
                                              author=TestViewPosts.user1))
        self.authorized_client.get(
            reverse('profile_unfollow',
                    kwargs={'username': TestViewPosts.user1})
        )
        self.assertFalse(Follow.objects.filter(user=TestViewPosts.user,
                                               author=TestViewPosts.user1))

    def test_follow_page(self):
        Follow.objects.create(user=TestViewPosts.user,
                              author=TestViewPosts.user1)
        request_follow_user_before_post = self.authorized_client.get(
            reverse('follow_index')).context['page'].object_list.__len__()
        request_unfollow_user_before_post = self.authorized_client2.get(
            reverse('follow_index')).context['page'].object_list.__len__()
        Post.objects.create(author=TestViewPosts.user1, text='test')
        request_follow_user_after_post = self.authorized_client.get(
            reverse('follow_index')).context['page'].object_list.__len__()
        request_unfollow_user_after_post = self.authorized_client2.get(
            reverse('follow_index')).context['page'].object_list.__len__()
        self.assertNotEqual(request_follow_user_before_post,
                            request_follow_user_after_post)
        self.assertEqual(request_unfollow_user_before_post,
                         request_unfollow_user_after_post)

    def test_comments(self):
        request_auth = self.authorized_client.get(
            reverse('add_comment', kwargs={'username': TestViewPosts.user,
                                           'post_id': TestViewPosts.post.id}))
        request_guest = self.guest_client.get(
            reverse('add_comment', kwargs={'username': TestViewPosts.user,
                                           'post_id': TestViewPosts.post.id}))
        self.assertEqual(request_auth.status_code, HTTPStatus.OK)
        self.assertEqual(request_guest.status_code, HTTPStatus.FOUND)


class TestPaginatorPosts(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(slug='test-slug')
        for i in range(15):
            cls.post = Post.objects.create(
                text=f'Test{i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self) -> None:
        cache.clear()

    def test_first_paginator_page_index(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(
            response.context.get('page').object_list.__len__(), 10
        )

    def test_second_paginator_page_index(self):
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(response.context.get('page').object_list.__len__(), 5)

    def test_first_paginator_page_group(self):
        response = self.client.get(reverse(
            'group_posts', kwargs={'slug': TestPaginatorPosts.group.slug})
        )
        self.assertEqual(
            response.context.get('page').object_list.__len__(), 10
        )

    def test_second_paginator_page_group(self):
        response = self.client.get(reverse(
            'group_posts',
            kwargs={'slug': TestPaginatorPosts.group.slug}) + '?page=2'
        )
        self.assertEqual(response.context.get('page').object_list.__len__(), 5)

    def test_first_paginator_page_profile(self):
        response = self.client.get(reverse(
            'profile', kwargs={'username': TestPaginatorPosts.user})
        )
        self.assertEqual(
            response.context.get('page').object_list.__len__(), 10
        )

    def test_second_paginator_page_profile(self):
        response = self.client.get(reverse(
            'profile',
            kwargs={'username': TestPaginatorPosts.user}) + '?page=2'
        )
        self.assertEqual(response.context.get('page').object_list.__len__(), 5)


class TestExistencePosts(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(slug='test-slug')
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.user = TestExistencePosts.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_existence_index(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(
            response.context['page'][0].group, TestExistencePosts.group
        )

    def test_post_existence_group_page(self):
        response = self.client.get(reverse(
            'group_posts', kwargs={'slug': TestExistencePosts.group.slug})
        )
        self.assertEqual(
            response.context['page'][0].group, TestExistencePosts.group
        )
