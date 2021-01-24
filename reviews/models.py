from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Review(models.Model):
    class StatusChoices(models.TextChoices):
        PUBLISHED = 'published', _('Published')
        NEW = 'new', _('New')
        HIDDEN = 'hidden', _('Hidden')

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(blank=True, null=True, default=None)
    status = models.CharField(
        max_length=9,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
    )

    def __str__(self):
        return f'Review of {self.author}'
