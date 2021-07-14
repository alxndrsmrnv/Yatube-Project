import shutil
from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.forms import PostForm
from posts.models import Post, User, Group


class TestFormPosts(TestCase):
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
        cls.group = Group.objects.create(slug='test-slug')
        cls.group1 = Group.objects.create(slug='test-slug1')
        cls.post = Post.objects.create(
            text='Test',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> None:
        self.guest_client = Client()
        self.user = TestFormPosts.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_form(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Test',
            'group': TestFormPosts.group1.id
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.filter(text=form_data['text'],
                                       group=form_data['group'])[0]
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            (form_data['text'], form_data['group']),
            (new_post.text, new_post.group.id))

    def test_edit_form(self):
        form_data = {
            'text': 'EditText',
            'group': TestFormPosts.group1.id
        }
        response = self.authorized_client.post(
            reverse(
                'post_edit', kwargs={'username': TestFormPosts.user,
                                     'post_id': TestFormPosts.post.id}),
                data=form_data,
                follow=True
        )
        edit_post = Post.objects.filter(text=form_data['text'],
                                        group=form_data['group'])[0]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), 1)
        self.assertNotEqual(
            (edit_post.group.slug, edit_post.text),
            (TestFormPosts.post.group.slug, TestFormPosts.post.text))

    def test_image_save(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'test',
            'group': TestFormPosts.group.id,
            'image': TestFormPosts.uploaded
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
