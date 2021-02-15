from copy import deepcopy

from django.urls import reverse, resolve
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from users.models import User
from users.serializers import UserSerializer


class UserCurrentRetrieveUpdateAPIViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.url = reverse('current')

    def setUp(self):
        self.view = resolve(self.url).func.cls.as_view()
        self.user_raw = {
            'first_name': 'Dably',
            'last_name': 'Ertov',
            'middle_name': 'Sergeevich',
            'phone': '+79999999999',
            'address': 'Moscow',
        }
        self.users = []
        self.users.append(User.objects.create(username='vanya', email='vanya@test.test', **self.user_raw))
        self.users.append(User.objects.create(username='sasha', email='sasha@test1.test', **self.user_raw))
        for user in self.users:
            user.set_password('87654321')
            user.save()

    def test_unauthorized_get(self):
        request = self.factory.get(self.url)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_unauthorized_put(self):
        request = self.factory.put(self.url, self.user_raw)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_unauthorized_patch(self):
        request = self.factory.patch(self.url, self.user_raw)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {'detail': 'Authentication credentials were not provided.'})

    def test_db(self):
        self.assertEqual(User.objects.count(), 2)
        users = User.objects.all()
        for user in users:
            user_raw = deepcopy(self.user_raw)
            if user.pk == 1:
                user_raw.update({'id': 1, 'username': 'vanya', 'email': 'vanya@test.test'})
            if user.pk == 2:
                user_raw.update({'id': 2, 'username': 'sasha', 'email': 'sasha@test1.test'})
            self.assertTrue(user.check_password('87654321'))
            user_data = UserSerializer(user).data
            self.assertEqual(user_raw, user_data)

    def test_retrieve(self):
        request = self.factory.get(self.url)
        force_authenticate(request, user=self.users[1])
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = UserSerializer(User.objects.get(pk=self.users[1].pk)).data
        self.assertEqual(response.data, user_data)

    def test_update(self):
        user_raw = {
            'email': 'vanya@test.test',
            'password': '87654321',
            'first_name': 'Vanya',
            'last_name': 'Vatrov',
            'middle_name': 'Aleeesss',
            'phone': '+79999998888',
            'address': 'St-pb',
        }
        request = self.factory.put(self.url, user_raw)
        force_authenticate(request, user=self.users[0])
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(pk=self.users[0].pk)
        user_data = UserSerializer(user).data
        # check db
        self.assertEqual('vanya', user.username)
        self.assertEqual(user_raw['email'], user.email)
        self.assertEqual(user_raw['first_name'], user.first_name)
        self.assertEqual(user_raw['last_name'], user.last_name)
        self.assertEqual(user_raw['middle_name'], user.middle_name)
        self.assertEqual(user_raw['phone'], user.phone)
        self.assertEqual(user_raw['address'], user.address)
        self.assertTrue(user.check_password(user_raw['password']))
        # check response
        self.assertEqual(response.data, user_data)

        # empty data
        user_raw = {}
        request = self.factory.put(self.url, user_raw)
        force_authenticate(request, user=self.users[0])
        response = self.view(request)
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

    def test_partial_update(self):
        # empty data
        user_raw = {}
        request = self.factory.patch(self.url, user_raw)
        force_authenticate(request, user=self.users[1])
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = UserSerializer(User.objects.get(pk=self.users[1].pk)).data
        self.assertEqual(response.data, user_data)

        # some data
        user_raw['email'] = 'tolkov@mail.ru'
        user_raw['middle_name'] = 'Geerreen'
        request = self.factory.patch(self.url, user_raw)
        force_authenticate(request, user=self.users[1])
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = UserSerializer(User.objects.get(pk=self.users[1].pk)).data
        self.assertEqual('tolkov', user_data['username'])
        self.assertEqual(user_raw['email'], user_data['email'])
        self.assertEqual(user_raw['middle_name'], user_data['middle_name'])
        self.assertEqual(response.data, user_data)

    def test_validation(self):
        # duplicate email, invalid phone
        user_raw = {
            'email': 'sasha@test1.test',
            'phone': 'hello',
        }
        request = self.factory.patch(self.url, user_raw)
        force_authenticate(request, user=self.users[0])
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "email": ["This field must be unique."],
                "phone": ["The phone number entered is not valid."],
            },
        )

        # invalid email
        user_raw = {
            'email': 'sasha',
        }
        request = self.factory.patch(self.url, user_raw)
        force_authenticate(request, user=self.users[0])
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "email": ["Enter a valid email address."],
            },
        )
