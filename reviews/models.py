from django.db import models

from users.models import User


class Review(models.Model):
    class StatusChoices(models.TextChoices):
        PUBLISHED = 'pub', _('Опубликован')
        ON_MODERATION = 'mod', _('На модерации')
        REJECTED = 'rej', _('Отклонен')

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vacancies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField()
    status = models.CharField(
        max_length=4,
        choices=StatusChoices.choices,
        default=StatusChoices.ON_MODERATION,)

    def __str__(self):
        return f'Review of {self.author}'
