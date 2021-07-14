from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.urls import reverse

from yatube.settings import PAGINATOR_CONST

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, PAGINATOR_CONST)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_list = group.posts.all()
    paginator = Paginator(group_list, PAGINATOR_CONST)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page, 'group': group}
    return render(request, 'group.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    profile_list = author.posts.all()
    paginator = Paginator(profile_list, PAGINATOR_CONST)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    post_user_count = author.posts.all().count()
    following = True
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()
    context = {'page': page, 'post_user_count': post_user_count,
               'author': author, 'following': following}
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    comments = post.comments.all()
    form = CommentForm()
    post_user_count = post.author.posts.all().count()
    context = {
        'post_user_count': post_user_count,
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'post.html', context)


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'new.html', {'form': form})
    form = PostForm()
    context = {'form': form, 'title': 'Новая запись',
               'header': 'Добавить запись', 'button': 'Добавить'}
    return render(request, 'new.html', context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post', username, post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        post.save()
        return redirect('post', username, post_id)
    context = {'form': form, 'post': post, 'title': 'Редактировать запись',
               'header': 'Редактировать', 'button': 'Сохранить'}
    return render(request, 'new.html', context)


def add_comment(request, username, post_id):
    if request.user.is_authenticated is False:
        return redirect('/auth/login/')
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('post', username, post_id)
    context = {'form': form, 'post': post}
    return render(request, 'comments.html', context)


@login_required
def follow_index(request):
    user_that_follows = get_object_or_404(User, username=request.user)
    follow_posts = Post.objects.filter(
        author__following__user=user_that_follows)
    paginator = Paginator(follow_posts, PAGINATOR_CONST)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {'page': page}
    return render(request, "follow.html", context)


@login_required
def profile_follow(request, username):
    path = reverse('profile', kwargs={'username': username})
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect(path)


@login_required
def profile_unfollow(request, username):
    path = reverse('profile', kwargs={'username': username})
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect(path)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
