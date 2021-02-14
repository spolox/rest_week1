from copy import deepcopy

from django.urls import reverse, resolve
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from users.models import User
from users.serializers import UserSerializer


class UserRegisterCreateAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.url = reverse('register')

    def setUp(self):
        self.view = resolve(self.url).func.cls.as_view()
        self.user_raw = {
            'email': 'vanya@test.test',
            'first_name': 'Dably',
            'last_name': 'Ertov',
            'middle_name': 'Sergeevich',
            'phone': '+79999999999',
            'address': 'Moscow',
        }
        self.user = User.objects.create(username='vanya', **self.user_raw)
        self.user.set_password('12345678')
        self.user.save()

    def test_db(self):
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(pk=self.user.pk)
        user_data = UserSerializer(user).data
        user_raw = deepcopy(self.user_raw)
        user_raw['username'] = 'vanya'
        user_raw['id'] = user.pk
        self.assertTrue(user.check_password('12345678'))
        self.assertEqual(user_raw, user_data)

    def test_create(self):
        # empty data
        user_raw = {}
        request = self.factory.post(self.url, user_raw)
        response = self.view(request)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "email": ["This field is required."],
                "password": ["This field is required."],
                "first_name": ["This field is required."],
                "last_name": ["This field is required."],
                "middle_name": ["This field is required."],
                "phone": ["This field is required."],
                "address": ["This field is required."],
            },
        )

        # invalid phone and duplicate email
        user_raw = deepcopy(self.user_raw)
        user_raw['password'] = '87654321'
        user_raw['phone'] = '+7123'
        request = self.factory.post(self.url, user_raw)
        response = self.view(request)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "email": ["This field must be unique."],
                "phone": ["The phone number entered is not valid."],
            },
        )

        # invalid email
        user_raw['email'] = 'sasha'
        user_raw['phone'] = '+7999 999 99 99'
        request = self.factory.post(self.url, user_raw)
        response = self.view(request)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "email": ["Enter a valid email address."],
            },
        )

        # valid data
        user_raw['email'] = 'seeer@mail.com'
        request = self.factory.post(self.url, user_raw)
        response = self.view(request)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['id'])
        user = User.objects.get(pk=response.data['id'])
        user_data = UserSerializer(user).data
        # check db
        self.assertEqual('seeer', user.username)
        self.assertEqual(user_raw['email'], user.email)
        self.assertEqual(user_raw['first_name'], user.first_name)
        self.assertEqual(user_raw['last_name'], user.last_name)
        self.assertEqual(user_raw['middle_name'], user.middle_name)
        self.assertEqual(user_raw['phone'], user.phone)
        self.assertEqual(user_raw['address'], user.address)
        self.assertTrue(user.check_password(user_raw['password']))
        # check response
        self.assertEqual(response.data, user_data)
