from copy import deepcopy
from datetime import timedelta

from django.urls import reverse, resolve
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, APIRequestFactory, force_authenticate

from carts.models import Cart
from carts.models import CartItem
from carts.serializers import CartItemSerializer
from items.models import Item
from items.serializers import ItemSerializer
from orders.models import Order
from users.models import User
from users.serializers import UserSerializer


class OrderViewSetListTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url_list = reverse('orders-list')
        cls.factory = APIRequestFactory()

    def setUp(self):
        self.view_list = resolve(self.url_list).func.cls.as_view(actions={'get': 'list', 'post': 'create'})
        self.item_raw = {
            'title': 'title 1',
            'description': 'description 1',
            'image': 'test_image.img',
            'weight': 100,
            'price': 500,
        }
        self.item = Item.objects.create(
            **self.item_raw
        )
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

        self.delivery_at = timezone.now()
        self.delivery_at += timedelta(hours=2)
        for i in range(1, 8):
            cart = self.user.my_cart
            CartItem.objects.create(
                item=self.item,
                quantity=i,
                price=self.item.price,
                cart=cart,
            )
            Order.objects.create(
                address=f'Moscow {i}',
                delivery_at=self.delivery_at,
                recipient=self.user,
                cart=cart,
                total_cost=cart.total_cost,
            )
        cart = self.user.my_cart
        CartItem.objects.create(
            item=self.item,
            quantity=8,
            price=self.item.price,
            cart=cart,
        )
        Order.objects.create(
            address='Moscow 8',
            delivery_at=self.delivery_at,
            recipient=self.user,
            cart=cart,
            total_cost=cart.total_cost,
            status=Order.StatusChoices.DELIVERED
        )
        cart = self.user.my_cart
        CartItem.objects.create(
            item=self.item,
            quantity=9,
            price=self.item.price,
            cart=cart,
        )
        Order.objects.create(
            address='Moscow 9',
            delivery_at=self.delivery_at,
            recipient=self.user,
            cart=cart,
            total_cost=cart.total_cost,
            status=Order.StatusChoices.PROCESSED
        )
        cart = self.user.my_cart
        CartItem.objects.create(
            item=self.item,
            quantity=10,
            price=self.item.price,
            cart=cart,
        )
        Order.objects.create(
            address='Moscow 10',
            delivery_at=self.delivery_at,
            recipient=self.user,
            cart=cart,
            total_cost=cart.total_cost,
            status=Order.StatusChoices.CANCELLED
        )

    def test_db(self):
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Cart.objects.count(), 10)
        self.assertEqual(CartItem.objects.count(), 10)
        self.assertEqual(Order.objects.count(), 10)

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

        carts = Cart.objects.all().order_by('cart_items__quantity')
        index = 1
        for cart in carts:
            self.assertEqual(cart.user, user)
            cart_item = CartItem.objects.get(cart=cart)
            self.assertEqual(cart_item.item, item)
            self.assertEqual(cart_item.quantity, index)
            self.assertEqual(cart_item.price, item.price)
            self.assertEqual(cart_item.cart, cart)
            self.assertEqual(cart_item.total_price, index * item.price)
            self.assertEqual(cart.total_cost, cart_item.total_price)
            index += 1

        orders = Order.objects.all().order_by('cart__cart_items__quantity')
        index = 1
        for order in orders:
            cart = Cart.objects.get(cart_items__quantity=index)

            if order.address == 'Moscow 8':
                self.assertEqual(order.status, Order.StatusChoices.DELIVERED)
            elif order.address == 'Moscow 9':
                self.assertEqual(order.status, Order.StatusChoices.PROCESSED)
            elif order.address == 'Moscow 10':
                self.assertEqual(order.status, Order.StatusChoices.CANCELLED)
            else:
                self.assertEqual(order.status, Order.StatusChoices.CREATED)
            self.assertEqual(order.recipient, self.user)
            self.assertEqual(order.delivery_at, self.delivery_at)
            self.assertEqual(order.cart, cart)
            self.assertEqual(order.total_cost, cart.total_cost)
            index += 1

    def test_unauthorized_list(self):
        request = self.factory.get(self.url_list)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_unauthorized_retrieve(self):
        url_detail = reverse('orders-detail', kwargs={'pk': 1})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_unauthorized_create(self):
        request = self.factory.post(self.url_list)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_unauthorized_update(self):
        url_detail = reverse('orders-detail', kwargs={'pk': 1})
        response = self.client.put(url_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_unauthorized_partial_update(self):
        url_detail = reverse('orders-detail', kwargs={'pk': 1})
        response = self.client.patch(url_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_pagination(self):
        request = self.factory.get(self.url_list)
        force_authenticate(request, self.user)
        response = self.view_list(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertIsNone(response.data['previous'])
        self.assertIn('/api/v1/orders/?limit=6&offset=6', response.data['next'])
        self.assertEqual(len(response.data['results']), 6)
        request = self.factory.get(response.data['next'])
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertIsNone(response.data['next'])
        self.assertIn('/api/v1/orders/?limit=6', response.data['previous'])
        self.assertEqual(len(response.data['results']), 4)

        # check max limit
        request = self.factory.get(self.url_list + '?limit=7')
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 6)

        request = self.factory.get(self.url_list + '?limit=5')
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

        # check min limit
        request = self.factory.get(self.url_list + '?limit=0')
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 6)

        # with offset
        request = self.factory.get(self.url_list + '?limit=6&offset=3')
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('/api/v1/orders/?limit=6&offset=9', response.data['next'])
        self.assertIn('/api/v1/orders/?limit=6', response.data['previous'])
        self.assertEqual(len(response.data['results']), 6)

        request = self.factory.get(self.url_list + '?limit=6&offset=5')
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['next'])
        self.assertIn('/api/v1/orders/?limit=6', response.data['previous'])
        self.assertEqual(len(response.data['results']), 5)

    def test_list(self):
        ...

    def test_retrieve(self):
        ...

    def test_create(self):
        ...

    def test_update(self):
        ...

    def test_partial_update(self):
        ...

    def test_validation(self):
        ...

