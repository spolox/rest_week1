from django.conf import settings
from django.db import models


class Item(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(
        upload_to=settings.MEDIA_ITEMS_IMAGE_DIR,
    )
    weight = models.IntegerField()
    price = models.DecimalField(decimal_places=2, max_digits=8)

    def __str__(self):
        return self.title
