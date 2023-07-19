from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name'
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=settings.LENGTH_TEXT_150
    )
    last_name = models.CharField(
        max_length=settings.LENGTH_TEXT_150,
        verbose_name='Фамилия',
    )
    email = models.EmailField(
        max_length=settings.LENGTH_TEXT_150,
        verbose_name='email',
        unique=True
    )
    username = models.CharField(
        verbose_name='username',
        max_length=settings.LENGTH_TEXT_150,
        unique=True,
        validators=(UnicodeUsernameValidator(),)
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='following'
    )

    class Meta:
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_follow'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
