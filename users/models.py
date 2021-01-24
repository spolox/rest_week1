from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    middle_name = models.CharField(max_length=100)
    phone_number = PhoneNumberField()
    address = models.CharField(max_length=100)

    def __str__(self):
        return self.username
