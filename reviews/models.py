from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User


class Review(models.Model):
    class StatusChoices(models.TextChoices):
        PUBLISHED = 'published', _('Опубликован')
        NEW = 'new', _('На модерации')
        HIDDEN = 'hidden', _('Отклонен')

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vacancies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(blank=True, null=True, default=None)
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
    )

    def __str__(self):
        return f'Review of {self.author}'
