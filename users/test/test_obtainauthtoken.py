from copy import deepcopy

from django.urls import reverse, resolve
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from users.models import User
from users.serializers import UserSerializer


class ObtainAuthTokenTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.url = reverse('login')
        cls.user_raw = {
            'email': 'vanya@test.test',
            'first_name': 'Dably',
            'last_name': 'Ertov',
            'middle_name': 'Sergeevich',
            'phone': '+79999999999',
            'address': 'Moscow',
        }
        cls.user = User.objects.create(username='vanya', **cls.user_raw)
        cls.user.set_password('55555555')
        cls.user.save()

    def setUp(self):
        self.view = resolve(self.url).func.cls.as_view()

    def test_db(self):
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(pk=self.user.pk)
        user_data = UserSerializer(user).data
        user_raw = deepcopy(self.user_raw)
        user_raw['id'] = user_data['id']
        user_raw['username'] = 'vanya'
        self.assertTrue(user.check_password('55555555'))
        self.assertEqual(user_raw, user_data)

    def test_login(self):
        # invalid password
        user_raw = {
            'username': 'vanya',
            'password': '12345',
        }
        request = self.factory.post(self.url, user_raw)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"non_field_errors": ["Unable to log in with provided credentials."]})

        # invalid username
        user_raw = {
            'username': 'vany',
            'password': '55555555',
        }
        request = self.factory.post(self.url, user_raw)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"non_field_errors": ["Unable to log in with provided credentials."]})

        # valid data
        user_raw = {
            'username': 'vanya',
            'password': '55555555',
        }
        request = self.factory.post(self.url, user_raw)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
