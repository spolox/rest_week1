from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Item


@receiver([post_save, post_delete], sender=Item)
def invalidate_item_cache(sender, **kwargs):
    cache.clear()
