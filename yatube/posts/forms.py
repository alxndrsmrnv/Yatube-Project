from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        label = {'text': 'Поле для заполнения', 'group': 'Группы'}
        help_text = 'Форма поста'


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        label = {'text': 'Поле комментария'}
        help_text = 'Форма комментариев'
