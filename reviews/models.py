from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Review(models.Model):
    class StatusChoices(models.TextChoices):
        PUBLISHED = 'published', _('published')
        NEW = 'new', _('new')
        HIDDEN = 'hidden', _('hidden')

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(blank=True, null=True, default=None)
    status = models.CharField(
        max_length=9,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
    )

    def save(self, *args, **kwargs):
        if self.status == self.StatusChoices.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super(Review, self).save(*args, **kwargs)

    def __str__(self):
        return f'Review of {self.author}'
