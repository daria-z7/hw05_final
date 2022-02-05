from xmlrpc.client import boolean
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404, get_list_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm

page_count = settings.PER_PAGE_COUNT


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, page_count)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.post_set.all()
    paginator = Paginator(posts, page_count)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    post_count = posts.count()
    paginator = Paginator(posts, page_count)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following: bool = False
    if request.user.is_authenticated and request.user != author:
        follower = Follow.objects.filter(user=request.user, author=author).exists() 
        if follower is True:
            following = True
    context = {
        'page_obj': page_obj,
        'post_count': post_count,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_count = Post.objects.filter(author=post.author).count()
    comment_form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'post_count': post_count,
        'comment_form': comment_form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):

    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
        )

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user)

        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm()
    group = Group.objects.all()
    context = {
        'form': form,
        'group': group,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            post = form.save()
            return redirect('posts:post_detail', post_id=post_id)

        context = {
            'form': form,
            'is_edit': is_edit,
            'post_id': post_id,
        }
        template = 'posts/create_post.html'
        return render(request, template, context)

    form = PostForm(instance=post)

    context = {
        'form': form,
        'is_edit': is_edit,
        'post_id': post_id,
    }
    template = 'posts/create_post.html'
    return render(request, template, context)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)

@login_required
def follow_index(request):
    posts = Post.objects.filter(author__in=Follow.objects.filter(user=request.user).values_list('author_id'))
    paginator = Paginator(posts, page_count)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect('posts:profile', username=username)
    follower = Follow.objects.filter(user=request.user, author=author).exists()
    if follower is False:
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)

@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect('posts:profile', username=username)
    follower = Follow.objects.filter(user=request.user, author=author).exists()
    if follower:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
