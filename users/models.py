from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from carts.models import Cart


class User(AbstractUser):
    middle_name = models.CharField(max_length=100)
    phone = PhoneNumberField()
    address = models.CharField(max_length=100)

    def __str__(self):
        return self.username

    @property
    def my_cart(self):
        cart, _ = Cart.objects.filter(user=self, order=None).get_or_create(user=self)
        return cart

    @property
    def public_name(self):
        return f'{self.last_name} {self.first_name}'
