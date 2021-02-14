from copy import deepcopy

from django.urls import reverse, resolve
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from carts.models import Cart
from carts.models import CartItem
from carts.serializers import CartItemSerializer
from carts.serializers import CartSerializer
from items.models import Item
from items.serializers import ItemSerializer
from users.models import User
from users.serializers import UserSerializer


class CartViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('cart')
        cls.factory = APIRequestFactory()

        cls.item_raw = {
            'title': 'title 1',
            'description': 'description 1',
            'image': 'test_image.img',
            'weight': 100,
            'price': 500,
        }
        item = Item.objects.create(**cls.item_raw)
        cls.user_raw = {
            'email': 'vanya@test.test',
            'first_name': 'Dably',
            'last_name': 'Ertov',
            'middle_name': 'Sergeevich',
            'phone': '+79999999999',
            'address': 'Moscow',
        }
        cls.user = User.objects.create(username='vanya', **cls.user_raw)
        cls.user.set_password('12345678')
        cls.user.save()
        cart = cls.user.my_cart
        CartItem.objects.create(
            item=item,
            quantity=5,
            price=item.price,
            cart=cart,
        )

    def setUp(self):
        self.view = resolve(self.url).func.cls.as_view(actions={'get': 'retrieve'})

    def test_db(self):
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(CartItem.objects.count(), 1)

        item = Item.objects.get()
        self.assertEqual(self.item_raw['title'], item.title)
        self.assertEqual(self.item_raw['description'], item.description)
        self.assertIn(self.item_raw['image'], item.image.url)
        self.assertEqual(self.item_raw['weight'], item.weight)
        self.assertEqual(self.item_raw['price'], item.price)

        user = User.objects.get()
        user_data = UserSerializer(user).data
        user_raw = deepcopy(self.user_raw)
        user_raw['id'] = user.pk
        user_raw['username'] = 'vanya'
        self.assertTrue(user.check_password('12345678'))
        self.assertEqual(user_raw, user_data)

        cart = Cart.objects.get()
        self.assertEqual(cart.user, user)

        cart_item = CartItem.objects.get()
        self.assertEqual(cart_item.item, item)
        self.assertEqual(cart_item.quantity, 5)
        self.assertEqual(cart_item.price, item.price)
        self.assertEqual(cart_item.cart, cart)
        self.assertEqual(cart_item.total_price, 5 * item.price)
        self.assertEqual(cart.total_cost, cart_item.total_price)

    def test_unauthorized(self):
        request = self.factory.get(self.url)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_retrieve(self):
        request = self.factory.get(self.url)
        force_authenticate(request, self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_data = CartSerializer(Cart.objects.get(pk=response.data['id'])).data
        self.assertEqual(response.data['total_cost'], cart_data['total_cost'])
        for cart_item_response in response.data['items']:
            cart_item_data = CartItemSerializer(CartItem.objects.get(pk=cart_item_response['id'])).data

            item_response = cart_item_response['item']
            item_data = ItemSerializer(Item.objects.get(pk=item_response['id'])).data

            del cart_item_response['item']
            del cart_item_data['item']
            self.assertEqual(dict(cart_item_response), cart_item_data)

            self.assertEqual(item_response['title'], item_data['title'])
            self.assertEqual(item_response['description'], item_data['description'])
            self.assertIn(item_data['image'], item_response['image'])
            self.assertEqual(item_response['weight'], item_data['weight'])
            self.assertEqual(item_response['price'], item_data['price'])


class CartViewSetEmptyCartTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('cart')
        cls.factory = APIRequestFactory()
        cls.user_raw = {
            'email': 'vanya@test.test',
            'first_name': 'Dably',
            'last_name': 'Ertov',
            'middle_name': 'Sergeevich',
            'phone': '+79999999999',
            'address': 'Moscow',
        }
        cls.user = User.objects.create(username='vanya', **cls.user_raw)
        cls.user.set_password('12345678')
        cls.user.save()

    def setUp(self):
        self.view = resolve(self.url).func.cls.as_view(actions={'get': 'retrieve'})

    def test_db(self):
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Cart.objects.count(), 0)

        user = User.objects.get()
        user_data = UserSerializer(user).data
        user_raw = deepcopy(self.user_raw)
        user_raw['id'] = user.pk
        user_raw['username'] = 'vanya'
        self.assertTrue(user.check_password('12345678'))
        self.assertEqual(user_raw, user_data)

    def test_retrieve_empty_cart(self):
        self.assertEqual(Cart.objects.count(), 0)
        request = self.factory.get(self.url)
        force_authenticate(request, self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Cart.objects.count(), 1)
        cart = Cart.objects.get()
        cart_data = CartSerializer(cart).data
        self.assertEqual(cart.user, self.user)
        self.assertEqual(response.data['id'], cart.id)
        self.assertEqual(response.data['items'], [])
        self.assertEqual(response.data['total_cost'], cart_data['total_cost'])
