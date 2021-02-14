from copy import deepcopy
from datetime import timedelta

from django.urls import reverse, resolve
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, APIRequestFactory, force_authenticate

from carts.models import Cart
from carts.models import CartItem
from carts.serializers import CartSerializer
from items.models import Item
from items.serializers import ItemSerializer
from orders.models import Order
from orders.serializers import OrderSerializer, OrderRetrieveUpdateSerializer
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
        self.item = Item.objects.create(**self.item_raw)
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
            status=Order.StatusChoices.DELIVERED,
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
            status=Order.StatusChoices.PROCESSED,
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
            status=Order.StatusChoices.CANCELLED,
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
        request = self.factory.get(self.url_list)
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_orders = response.data['results']
        request = self.factory.get(response.data['next'])
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_orders += response.data['results']

        self.assertEqual(len(response_orders), 10)

        for response_order in response_orders:
            order_data = OrderSerializer(Order.objects.get(pk=response_order['id'])).data
            self.assertEqual(dict(order_data), response_order)

    def test_retrieve(self):
        order = Order.objects.latest('id')

        # bad pk
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk+1})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

        # good pk
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order_data = OrderRetrieveUpdateSerializer(order).data

        self.assertEqual(response.data['id'], order_data['id'])
        self.assertEqual(response.data['status'], order_data['status'])
        self.assertEqual(response.data['recipient'], order_data['recipient'])
        self.assertEqual(response.data['total_cost'], order_data['total_cost'])
        self.assertEqual(response.data['address'], order_data['address'])
        self.assertEqual(response.data['delivery_at'], order_data['delivery_at'])
        self.assertEqual(response.data['created_at'], order_data['created_at'])

        response_cart = response.data['cart']
        cart_data = CartSerializer(Cart.objects.get(pk=response_cart['id']))
        self.assertEqual(response_cart['total_cost'], cart_data['total_cost'].value)

        response_cart_items = response_cart['items']
        for response_cart_item in response_cart_items:
            cart_item = CartItem.objects.get(pk=response_cart_item['id'])
            self.assertEqual(response_cart_item['quantity'], cart_item.quantity)
            self.assertEqual(float(response_cart_item['price']), cart_item.price)
            self.assertEqual(float(response_cart_item['total_price']), cart_item.total_price)

            response_item = response_cart_item['item']
            item_data = ItemSerializer(Item.objects.get(pk=response_item['id'])).data
            self.assertEqual(response_cart_item['item_id'], item_data['id'])
            self.assertEqual(response_item['title'], item_data['title'])
            self.assertEqual(response_item['description'], item_data['description'])
            self.assertIn(item_data['image'], response_item['image'])
            self.assertEqual(response_item['weight'], item_data['weight'])
            self.assertEqual(response_item['price'], item_data['price'])

    def test_create(self):
        # in initial data we don't have free cart, all carts are blocks
        order_raw = {
            'address': 'Mosc',
            'delivery_at': str(timezone.now() + timedelta(hours=1)),
        }

        self.assertEqual(Cart.objects.count(), 10)
        request = self.factory.post(self.url_list, order_raw)
        force_authenticate(request, self.user)
        response = self.view_list(request)

        # after post we get free cart, but cart is empty
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Your cart is empty"})
        self.assertEqual(Cart.objects.count(), 11)

        cart = self.user.my_cart

        # we added new items to cart
        cart_item = CartItem.objects.create(
            item=self.item,
            quantity=5,
            price=self.item.price,
            cart=cart,
        )
        # check db
        cart_item = CartItem.objects.get(cart=cart)
        self.assertEqual(cart_item.item, self.item)
        self.assertEqual(cart_item.quantity, 5)
        self.assertEqual(cart_item.price, self.item.price)
        self.assertEqual(cart_item.total_price, self.item.price * 5)

        # empty data
        order_raw = {}
        request = self.factory.post(self.url_list, order_raw)
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                'address': ['This field is required.'],
                'delivery_at': ['This field is required.'],
            },
        )

        # good data
        order_raw = {
            'address': 'Mosc',
            'delivery_at': str(timezone.now() + timedelta(hours=1)),
        }
        request = self.factory.post(self.url_list, order_raw)
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(pk=response.data['id'])

        self.assertEqual(order_raw['address'], order.address)
        self.assertEqual(parse_datetime(order_raw['delivery_at']), order.delivery_at)
        self.assertEqual(response.data['status'], order.status)
        self.assertEqual(response.data['cart'], order.cart.pk)
        self.assertEqual(float(response.data['total_cost']), float(order.total_cost))
        self.assertEqual(response.data['address'], order.address)
        self.assertEqual(parse_datetime(response.data['delivery_at']), order.delivery_at)
        self.assertEqual(parse_datetime(response.data['created_at']), order.created_at)

    def test_update(self):
        # other status are testing in test_validation
        order = Order.objects.filter(status=Order.StatusChoices.CREATED).first()

        # bad pk
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk + 100})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

        # empty data
        order_raw = {}
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                'status': ['This field is required.'],
                'address': ['This field is required.'],
                'delivery_at': ['This field is required.'],
            },
        )

        # good data, status not change
        order_raw = {
            'status': 'created',
            'address': 'Sssootttt',
            'delivery_at': str(timezone.now() + timedelta(hours=5)),
        }
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail, order_raw)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order = Order.objects.get(pk=response.data['id'])
        self.assertEqual(order_raw['status'], order.status)
        self.assertEqual(order_raw['address'], order.address)
        self.assertEqual(parse_datetime(order_raw['delivery_at']), order.delivery_at)

        order_data = OrderRetrieveUpdateSerializer(order).data

        self.assertEqual(response.data['id'], order_data['id'])
        self.assertEqual(response.data['status'], order_data['status'])
        self.assertEqual(response.data['recipient'], order_data['recipient'])
        self.assertEqual(response.data['total_cost'], order_data['total_cost'])
        self.assertEqual(response.data['address'], order_data['address'])
        self.assertEqual(response.data['delivery_at'], order_data['delivery_at'])
        self.assertEqual(response.data['created_at'], order_data['created_at'])

        response_cart = response.data['cart']
        cart_data = CartSerializer(Cart.objects.get(pk=response_cart['id']))
        self.assertEqual(response_cart['total_cost'], cart_data['total_cost'].value)

        response_cart_items = response_cart['items']
        for response_cart_item in response_cart_items:
            cart_item = CartItem.objects.get(pk=response_cart_item['id'])
            self.assertEqual(response_cart_item['quantity'], cart_item.quantity)
            self.assertEqual(float(response_cart_item['price']), cart_item.price)
            self.assertEqual(float(response_cart_item['total_price']), cart_item.total_price)

            response_item = response_cart_item['item']
            item_data = ItemSerializer(Item.objects.get(pk=response_item['id'])).data
            self.assertEqual(response_cart_item['item_id'], item_data['id'])
            self.assertEqual(response_item['title'], item_data['title'])
            self.assertEqual(response_item['description'], item_data['description'])
            self.assertIn(item_data['image'], response_item['image'])
            self.assertEqual(response_item['weight'], item_data['weight'])
            self.assertEqual(response_item['price'], item_data['price'])

        # good data, status is change to cancelled
        order_raw = {
            'status': 'cancelled',
            'address': 'Sssootttt',
            'delivery_at': str(timezone.now() + timedelta(hours=5)),
        }
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail, order_raw)
        order = Order.objects.get(pk=response.data['id'])
        self.assertEqual(order_raw['status'], order.status)
        self.assertEqual(response.data['status'], order.status)

    def test_partial_update(self):
        # other status are testing in test_validation
        order = Order.objects.filter(status=Order.StatusChoices.CREATED).first()

        # bad pk
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk + 100})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

        # empty data
        order_raw = {}
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, order_raw)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order = Order.objects.get(pk=response.data['id'])
        order_data = OrderRetrieveUpdateSerializer(order).data

        self.assertEqual(response.data['id'], order_data['id'])
        self.assertEqual(response.data['status'], order_data['status'])
        self.assertEqual(response.data['recipient'], order_data['recipient'])
        self.assertEqual(response.data['total_cost'], order_data['total_cost'])
        self.assertEqual(response.data['address'], order_data['address'])
        self.assertEqual(response.data['delivery_at'], order_data['delivery_at'])
        self.assertEqual(response.data['created_at'], order_data['created_at'])

        response_cart = response.data['cart']
        cart_data = CartSerializer(Cart.objects.get(pk=response_cart['id']))
        self.assertEqual(response_cart['total_cost'], cart_data['total_cost'].value)

        response_cart_items = response_cart['items']
        for response_cart_item in response_cart_items:
            cart_item = CartItem.objects.get(pk=response_cart_item['id'])
            self.assertEqual(response_cart_item['quantity'], cart_item.quantity)
            self.assertEqual(float(response_cart_item['price']), cart_item.price)
            self.assertEqual(float(response_cart_item['total_price']), cart_item.total_price)

            response_item = response_cart_item['item']
            item_data = ItemSerializer(Item.objects.get(pk=response_item['id'])).data
            self.assertEqual(response_cart_item['item_id'], item_data['id'])
            self.assertEqual(response_item['title'], item_data['title'])
            self.assertEqual(response_item['description'], item_data['description'])
            self.assertIn(item_data['image'], response_item['image'])
            self.assertEqual(response_item['weight'], item_data['weight'])
            self.assertEqual(response_item['price'], item_data['price'])

        # good data

        order_raw = {
            'address': 'Sssootttt',
        }
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, order_raw)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order = Order.objects.get(pk=response.data['id'])
        self.assertEqual(order_raw['address'], order.address)
        self.assertEqual(response.data['address'], order.address)

        order_raw = {
            'delivery_at': str(timezone.now() + timedelta(hours=5)),
        }
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, order_raw)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order = Order.objects.get(pk=response.data['id'])
        self.assertEqual(parse_datetime(order_raw['delivery_at']), order.delivery_at)
        self.assertEqual(parse_datetime(response.data['delivery_at']), order.delivery_at)

    def test_validation(self):
        # bad data with delivery_at
        order_raw = {
            'address': 'Mosc',
            'delivery_at': str(timezone.now() - timedelta(hours=1)),
        }
        request = self.factory.post(self.url_list, order_raw)
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'delivery_at': {'detail': 'You cannot set delivery_at earlier now time'}})

        # bad data with status for update
        order = Order.objects.filter(status=Order.StatusChoices.CREATED).first()
        order_raw = {
            'status': 'processed',
            'address': 'Mosc',
            'delivery_at': str(timezone.now() + timedelta(hours=1)),
        }
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail, order_raw)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'You can only set status as `cancelled`'})

        # cannot update if order is not created

        # order is processed
        order = Order.objects.get(status=Order.StatusChoices.PROCESSED)
        order_raw = {}
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, order_raw)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Your order is processed'})

        # order is delivered
        order = Order.objects.get(status=Order.StatusChoices.DELIVERED)
        order_raw = {}
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, order_raw)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Your order is delivered'})

        # order is cancelled
        order = Order.objects.get(status=Order.StatusChoices.CANCELLED)
        order_raw = {}
        url_detail = reverse('orders-detail', kwargs={'pk': order.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, order_raw)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Your order is cancelled'})
