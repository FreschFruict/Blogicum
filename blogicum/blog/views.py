from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Post, Category, Comment
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .forms import UserEditForm as EditUserForm
from django.db.models import Count
# from .forms import PostForm
# from django.http import HttpResponseForbidden


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт {username} создан!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registration_form.html',
                  {'form': form})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = (
        Post.objects
        .filter(author=user)
        .select_related('author')
        .order_by('-pub_date')
        .annotate(comment_count=Count('comments'))
    )

    # Пагинация
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': user,
        'page_obj': page_obj,
        'is_author': request.user == user,  # Для проверки владельца
    }
    return render(request, 'blog/profile.html', context)


@login_required
def profile_edit(request, username=None):
    if username is None:
        username = request.user.username

    if request.user.username != username:
        return redirect('blog:profile', username=username)

    print(f"Using EditUserForm: {EditUserForm}")
    print(f"EditUserForm module: {EditUserForm.__module__}")

    if request.method == 'POST':
        # Передаем instance в форму
        form = EditUserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлён!')
            return redirect('blog:profile',
                            username=form.cleaned_data['username'])
        else:
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.username = request.POST.get('username', user.username)
            user.save()
            messages.success(request, 'Профиль обновлён!')
            return redirect('blog:profile', username=user.username)
    else:
        # Для GET запроса создаем форму с instance
        form = EditUserForm(instance=request.user)

    return render(request, 'blog/user.html', {'form': form})


@login_required
def create_post(request):
    from .forms import PostForm
    from .models import Category

    categories = Category.objects.filter(is_published=True)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.is_published = True

            # Обработка категории если передана строкой
            category_input = request.POST.get('category')
            if category_input and not post.category:
                category = None
                try:
                    category = Category.objects.get(
                        title=category_input,
                        is_published=True
                    )
                except Category.DoesNotExist:
                    try:
                        category = Category.objects.get(
                            id=category_input,
                            is_published=True
                        )
                    except (Category.DoesNotExist, ValueError):
                        pass
                post.category = category

            post.save()
            messages.success(request, 'Пост успешно создан!')
            return redirect('blog:profile', username=request.user.username)
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = PostForm()

    return render(request, 'blog/create.html', {
        'categories': categories,
        'form': form
    })


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', id=post.id)

    if request.method == 'POST':
        post.title = request.POST.get('title')
        post.text = request.POST.get('text')
        pub_date_str = request.POST.get('pub_date')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

        from django.utils.dateparse import parse_datetime
        pub_date = parse_datetime(pub_date_str)
        if pub_date:
            post.pub_date = pub_date

        if category_id:
            from .models import Category
            try:
                post.category = Category.objects.get(id=category_id,
                                                     is_published=True)
            except Category.DoesNotExist:
                post.category = None
        else:
            post.category = None

        if image:
            post.image = image

        post.save()
        return redirect('blog:post_detail', id=post.id)

    from django import forms

    class PostEditForm(forms.ModelForm):
        class Meta:
            model = Post
            fields = ['title', 'text', 'pub_date', 'category', 'image']
            widgets = {
                'text': forms.Textarea(attrs={'rows': 5}),
                'pub_date': forms.DateTimeInput(
                    attrs={'type': 'datetime-local'}
                ),
            }

    form = PostEditForm(instance=post)

    from .models import Category
    categories = Category.objects.filter(is_published=True)
    pub_date_local = post.pub_date.strftime('%Y-%m-%dT%H:%M')

    return render(request, 'blog/create.html', {
        'post': post,
        'categories': categories,
        'pub_date_local': pub_date_local,
        'form': form
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        text = request.POST.get('text')
        if text and text.strip():  # Проверяем, что текст не пустой
            Comment.objects.create(
                post=post,
                author=request.user,
                text=text.strip()
            )
            messages.success(request, 'Комментарий добавлен!')
        else:
            messages.error(request, 'Текст комментария не может быть пустым')

    return redirect('blog:post_detail', id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if request.user != comment.author:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Доступ запрещен")

    if request.method == 'POST':
        comment.text = request.POST.get('text')
        comment.save()
        return redirect('blog:post_detail', id=post_id)

    from django import forms

    class CommentEditForm(forms.ModelForm):
        class Meta:
            model = Comment
            fields = ['text']
            widgets = {
                'text': forms.Textarea(attrs={'rows': 5}),
            }
            labels = {
                'text': 'Текст комментария',
            }

    # ModelForm автоматически работает с instance
    form = CommentEditForm(instance=comment)

    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if request.user != comment.author:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Доступ запрещен")

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=post_id)

    # Для удаления НЕ передаем форму
    return render(request, 'blog/comment.html', {
        'comment': comment
    })


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', id=post_id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    return render(request, 'blog/detail.html', {
        'post': post,
        'confirm_delete': True
    })


def index(request):
    post_list = (
        Post.objects
        .filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )
        .select_related('author', 'category')
        .prefetch_related('comments')
        .order_by('-pub_date')
        .annotate(comment_count=Count('comments'))
    )

    paginator = Paginator(post_list, 10)  # ← 10 постов на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, id):
    # Сначала получаем пост без фильтров
    post = get_object_or_404(Post, pk=id)

    # Проверяем права доступа для неопубликованных постов
    if not post.is_published:
        # Если пост не опубликован, проверяем авторство
        if request.user != post.author:
            # Для не-авторов неопубликованного поста - 404
            from django.http import Http404
            raise Http404("Пост не найден")
        # Автор может видеть свой неопубликованный пост

    # Проверяем права доступа для постов с неопубликованной категорией
    if post.category and not post.category.is_published:
        # Если категория не опубликована, проверяем авторство
        if request.user != post.author:
            # Для не-авторов поста с неопубликованной категорией - 404
            from django.http import Http404
            raise Http404("Пост не найден")
        # Автор может видеть свой пост даже с неопубликованной категорией

    # Проверяем отложенные публикации
    if post.is_published and post.pub_date > timezone.now():
        # Для отложенных постов проверяем авторство
        if request.user != post.author:
            from django.http import Http404
            raise Http404("Пост еще не опубликован")
        # Автор может видеть свой отложенный пост

    # Загружаем комментарии
    comments = post.comments.all()

    # Создаем форму для комментария
    from django import forms

    class CommentForm(forms.Form):
        text = forms.CharField(
            widget=forms.Textarea(attrs={'rows': 3}),
            label='Добавить комментарий'
        )

    form = CommentForm()

    return render(request, 'blog/detail.html', {
        'post': post,
        'form': form,
        'comments': comments
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True)
    post_list = (
        Post.objects.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
            category=category,
            # pub_date=timezone.now()
        )
        .select_related('author', 'category')
        .prefetch_related('comments')
        .order_by('-pub_date')
        .annotate(comment_count=Count('comments'))
    )
    paginator = Paginator(post_list, 10)  # ← 10 постов
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': page_obj,
    })
