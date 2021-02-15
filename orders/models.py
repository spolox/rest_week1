from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from carts.models import Cart


class Order(models.Model):
    class StatusChoices(models.TextChoices):
        CREATED = 'created', _('created')
        DELIVERED = 'delivered', _('delivered')
        PROCESSED = 'processed', _('processed')
        CANCELLED = 'cancelled', _('cancelled')

    created_at = models.DateTimeField(auto_now_add=True)
    delivery_at = models.DateTimeField()
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.CharField(max_length=256)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='order')
    status = models.CharField(
        max_length=9,
        choices=StatusChoices.choices,
        default=StatusChoices.CREATED,
    )
    total_cost = models.DecimalField(decimal_places=2, max_digits=8)

    def __str__(self):
        return f'Order of user {self.recipient.pk} for cart {self.cart.pk}'
