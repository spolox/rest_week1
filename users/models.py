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
        cart = Cart.objects.get_or_create(self)
        return cart
