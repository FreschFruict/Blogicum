from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    title = models.CharField(max_length=256, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(unique=True, verbose_name='Идентификатор',
                            help_text="Идентификатор страницы для URL"
                            "; разрешены символы латиницы, цифры"
                            ", дефис и подчёркивание.")
    is_published = models.BooleanField(default=True,
                                       verbose_name='Опубликовано',
                                       help_text="Снимите галочку"
                                       ", чтобы скрыть публикацию.")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Добавлено')

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title


class Location(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название места')
    is_published = models.BooleanField(default=True,
                                       verbose_name='Опубликовано',
                                       help_text="Снимите галочку"
                                       ", чтобы скрыть публикацию.")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Добавлено')

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=256, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(verbose_name='Дата и время публикации',
                                    help_text="Если установить дату и вре"
                                    "мя в будущем — можно делать отложе"
                                    "нные публикации.")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор публикации')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL,
                                 null=True, verbose_name='Местоположение')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                 null=True, verbose_name='Категория')
    is_published = models.BooleanField(default=True,
                                       verbose_name='Опубликовано',
                                       help_text="Снимите галочку"
                                       ", чтобы скрыть публикацию.")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Добавлено')

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Комментарий от {self.author.username}'
