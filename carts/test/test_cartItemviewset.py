from copy import deepcopy

from django.urls import reverse, resolve
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, APIRequestFactory, force_authenticate

from carts.models import Cart
from carts.models import CartItem
from carts.serializers import CartItemSerializer
from items.models import Item
from items.serializers import ItemSerializer
from users.models import User
from users.serializers import UserSerializer


class CartItemViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.url_list = reverse('cartitems-list')

    def setUp(self):
        self.view_list = resolve(self.url_list).func.cls.as_view(actions={'get': 'list', 'post': 'create'})
        self.item_raw = {
            'title': 'title 1',
            'description': 'description 1',
            'image': 'test_image.img',
            'weight': 100,
            'price': 500,
        }
        item = Item.objects.create(**self.item_raw)
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
        cart = self.user.my_cart
        for i in range(1, 11):
            CartItem.objects.create(
                item=item,
                quantity=i,
                price=item.price,
                cart=cart,
            )

    def test_db(self):
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Cart.objects.count(), 1)
        self.assertEqual(CartItem.objects.count(), 10)

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

        cart_items = CartItem.objects.all().order_by('quantity')
        index = 1
        total_cost = 0.
        for cart_item in cart_items:
            self.assertEqual(cart_item.item, item)
            self.assertEqual(cart_item.quantity, index)
            self.assertEqual(cart_item.price, item.price)
            self.assertEqual(cart_item.cart, cart)
            self.assertEqual(cart_item.total_price, index * item.price)
            total_cost += float(cart_item.total_price)
            index += 1
        self.assertEqual(float(cart.total_cost), total_cost)

    def test_unauthorized_list(self):
        request = self.factory.get(self.url_list)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_unauthorized_retrieve(self):
        url_detail = reverse('cartitems-detail', kwargs={'pk': 1})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_unauthorized_create(self):
        request = self.factory.post(self.url_list)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_unauthorized_update(self):
        url_detail = reverse('cartitems-detail', kwargs={'pk': 1})
        response = self.client.put(url_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_unauthorized_partial_update(self):
        url_detail = reverse('cartitems-detail', kwargs={'pk': 1})
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
        self.assertIn('/api/v1/carts/items/?limit=6&offset=6', response.data['next'])
        self.assertEqual(len(response.data['results']), 6)
        request = self.factory.get(response.data['next'])
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertIsNone(response.data['next'])
        self.assertIn('/api/v1/carts/items/?limit=6', response.data['previous'])
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
        self.assertIn('/api/v1/carts/items/?limit=6&offset=9', response.data['next'])
        self.assertIn('/api/v1/carts/items/?limit=6', response.data['previous'])
        self.assertEqual(len(response.data['results']), 6)

        request = self.factory.get(self.url_list + '?limit=6&offset=5')
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['next'])
        self.assertIn('/api/v1/carts/items/?limit=6', response.data['previous'])
        self.assertEqual(len(response.data['results']), 5)

    def test_list(self):
        request = self.factory.get(self.url_list)
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_cart_items = response.data['results']
        request = self.factory.get(response.data['next'])
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_cart_items += response.data['results']

        self.assertEqual(len(response_cart_items), 10)

        for response_cart_item in response_cart_items:
            cart_item = CartItem.objects.get(pk=response_cart_item['id'])
            cart_item_data = CartItemSerializer(cart_item).data
            item = Item.objects.get(pk=response_cart_item['item_id'])
            item_data = ItemSerializer(item).data
            self.assertEqual(cart_item.item, item)
            self.assertEqual(response_cart_item['quantity'], cart_item_data['quantity'])
            self.assertEqual(response_cart_item['price'], cart_item_data['price'])
            self.assertEqual(response_cart_item['total_price'], cart_item_data['total_price'])

            response_item = response_cart_item['item']
            self.assertEqual(response_item['title'], item_data['title'])
            self.assertEqual(response_item['description'], item_data['description'])
            self.assertIn(item_data['image'], response_item['image'])
            self.assertEqual(response_item['weight'], item_data['weight'])
            self.assertEqual(response_item['price'], item_data['price'])

    def test_retrieve(self):
        cart_item = CartItem.objects.latest('id')

        # invalid pk
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk + 1})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

        # valid pk
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item_data = CartItemSerializer(cart_item).data
        item = Item.objects.get(pk=response.data['item_id'])
        item_data = ItemSerializer(item).data
        self.assertEqual(cart_item.item, item)
        self.assertEqual(response.data['quantity'], cart_item_data['quantity'])
        self.assertEqual(response.data['price'], cart_item_data['price'])
        self.assertEqual(response.data['total_price'], cart_item_data['total_price'])

        response_item = response.data['item']
        self.assertEqual(response_item['title'], item_data['title'])
        self.assertEqual(response_item['description'], item_data['description'])
        self.assertIn(item_data['image'], response_item['image'])
        self.assertEqual(response_item['weight'], item_data['weight'])
        self.assertEqual(response_item['price'], item_data['price'])

    def test_create(self):
        self.assertEqual(CartItem.objects.count(), 10)

        # empty data
        cart_item_raw = {}
        request = self.factory.post(self.url_list, cart_item_raw)
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                'item_id': ['This field is required.'],
                'quantity': ['This field is required.'],
            },
        )
        self.assertEqual(CartItem.objects.count(), 10)

        item = Item.objects.get()

        # good data
        cart_item_raw = {
            'item_id': item.pk,
            'quantity': 10,
        }
        request = self.factory.post(self.url_list, cart_item_raw)
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.count(), 11)
        cart_item = CartItem.objects.get(pk=response.data['id'])
        cart_item_data = CartItemSerializer(cart_item).data
        item = Item.objects.get(pk=response.data['item_id'])
        item_data = ItemSerializer(item).data
        self.assertEqual(cart_item.item, item)
        self.assertEqual(response.data['quantity'], cart_item_data['quantity'])
        self.assertEqual(response.data['price'], cart_item_data['price'])
        self.assertEqual(response.data['total_price'], cart_item_data['total_price'])

        response_item = response.data['item']
        self.assertEqual(response_item['title'], item_data['title'])
        self.assertEqual(response_item['description'], item_data['description'])
        self.assertIn(item_data['image'], response_item['image'])
        self.assertEqual(response_item['weight'], item_data['weight'])
        self.assertEqual(response_item['price'], item_data['price'])

    def test_update(self):
        cart_item = CartItem.objects.latest('id')

        cart_item_raw = {
            'item_id': cart_item.item_id,
            'quantity': cart_item.quantity,
        }

        # bad pk
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk + 1})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

        # empty data
        cart_item_raw = {}
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                 'item_id': ['This field is required.'],
                 'quantity': ['This field is required.'],
            },
        )

        # good data
        quantity_new = cart_item.quantity + 2
        cart_item_raw = {
            'item_id': cart_item.item_id,
            'quantity': quantity_new,
        }
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item_data = CartItemSerializer(CartItem.objects.get(pk=response.data['id'])).data
        # check db
        self.assertEqual(cart_item_data['quantity'], quantity_new)
        self.assertEqual(float(cart_item_data['total_price']), 500. * quantity_new)
        # check response
        self.assertEqual(cart_item_data['quantity'], response.data['quantity'])
        self.assertEqual(cart_item_data['total_price'], response.data['total_price'])

        # change price of Item
        quantity_new = cart_item.quantity + 2

        item = Item.objects.get()
        # old price
        self.assertEqual(float(item.price), 500.)
        item.price = 1000
        item.save()
        item = Item.objects.get()
        # new price
        self.assertEqual(float(item.price), 1000.)

        cart_item = CartItem.objects.latest('id')
        # this must be old price of Item
        self.assertEqual(float(cart_item.price), 500.)

        # good data
        cart_item_raw = {
            'item_id': cart_item.item_id,
            'quantity': quantity_new,
        }
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item_data = CartItemSerializer(CartItem.objects.get(pk=response.data['id'])).data
        # check db
        self.assertEqual(cart_item_data['quantity'], quantity_new)
        self.assertEqual(float(cart_item_data['price']), 1000.)
        self.assertEqual(float(cart_item_data['total_price']), 1000. * quantity_new)
        # check response
        self.assertEqual(cart_item_data['quantity'], response.data['quantity'])
        self.assertEqual(cart_item_data['price'], response.data['price'])
        self.assertEqual(cart_item_data['total_price'], response.data['total_price'])

    def test_partial_update(self):
        cart_item = CartItem.objects.latest('id')

        cart_item_raw = {
            'item_id': cart_item.item_id,
            'quantity': cart_item.quantity,
        }

        # bad pk
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk + 1})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

        # empty data
        cart_item_raw = {}
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item_data = CartItemSerializer(CartItem.objects.get(pk=response.data['id'])).data
        self.assertEqual(response.data['quantity'], cart_item_data['quantity'])
        self.assertEqual(response.data['price'], cart_item_data['price'])
        self.assertEqual(response.data['total_price'], cart_item_data['total_price'])

        # good data
        cart_item_raw = {
            'quantity': 20,
        }
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item_data = CartItemSerializer(CartItem.objects.get(pk=response.data['id'])).data
        # check db
        self.assertEqual(cart_item_data['quantity'], 20)
        self.assertEqual(float(cart_item_data['total_price']), 20 * 500)
        # check response
        self.assertEqual(response.data['quantity'], cart_item_data['quantity'])
        self.assertEqual(response.data['total_price'], cart_item_data['total_price'])

    def test_validation(self):
        item = Item.objects.get()
        cart_item_raw = {
            'item_id': item.pk + 1,
            'quantity': 0,
        }
        request = self.factory.post(self.url_list, cart_item_raw)
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                'item_id': [f'Invalid pk "{item.pk + 1}" - object does not exist.'],
                'quantity': ['Ensure this value is greater than or equal to 1.'],
            },
        )


class CartItemViewSetDestroyTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

    def setUp(self):
        self.item_raw = {
            'title': 'title 1',
            'description': 'description 1',
            'image': 'test_image.img',
            'weight': 100,
            'price': 500,
        }
        item = Item.objects.create(**self.item_raw)
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
        cart = self.user.my_cart
        CartItem.objects.create(
            item=item,
            quantity=5,
            price=item.price,
            cart=cart,
        )

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
        url_detail = reverse('cartitems-detail', kwargs={'pk': 1})
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_destroy(self):
        self.assertEqual(CartItem.objects.count(), 1)
        cart_item = CartItem.objects.get()

        # invalid pk
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk + 1})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})
        self.assertEqual(CartItem.objects.count(), 1)

        # valid pk
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(response.data)
        self.assertEqual(CartItem.objects.count(), 0)


class CartItemViewSetEmptyCartTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('cartitems-list')
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
        self.view = resolve(self.url).func.cls.as_view(actions={'get': 'list'})

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
        self.assertEqual(cart.user, self.user)
        self.assertEqual(response.data['count'], 0)
        self.assertIsNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        self.assertEqual(response.data['results'], [])
