from django.conf import settings
from django.db import models

from items.models import Item


class Cart(models.Model):
    items = models.ManyToManyField(Item, through='CartItem')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'Cart {self.pk} of user {self.user.username}'

    @property
    def total_cost(self):
        total_cost = 0
        for cart_item in self.cart_items.all():
            total_cost += cart_item.total_price
        return total_cost


class CartItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(decimal_places=2, max_digits=8)

    def __str__(self):
        return f'CartItem {self.pk} of cart {self.cart.pk}'

    @property
    def total_price(self):
        return self.quantity * self.price
