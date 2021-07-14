from django.test.testcases import TestCase

from posts.models import Group, Post, User


class TestPostModel(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.post = Post.objects.create(
            text='Это задание будет проверено в конце спринта',
            pub_date='2021-07-05',
            author=cls.user
        )

    def test_text(self):
        self.assertEqual(TestPostModel.post.text[:15], str(TestPostModel.post))


class TestGroupModel(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test_title'
        )

    def test_title(self):
        self.assertEqual(TestGroupModel.group.title, str(TestGroupModel.group))
