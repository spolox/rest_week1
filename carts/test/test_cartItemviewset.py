from django.urls import reverse, resolve
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, APIRequestFactory, force_authenticate

from carts.models import Cart
from carts.models import CartItem
from items.models import Item
from users.models import User


class CartItemViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.url_list = reverse('cartitems-list')

    def setUp(self):
        self.view_list = resolve(self.url_list).func.cls.as_view(actions={'get': 'list', 'post': 'create'})
        self.item = Item.objects.create(
                title='title 1',
                description='description 1',
                image='test_image.img',
                weight=100,
                price=500,
        )
        self.user = User.objects.create(username='vanya')
        cart = self.user.my_cart
        self.cart_item = CartItem.objects.create(
            item=self.item,
            quantity=5,
            price=self.item.price,
            cart=cart,
        )

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
        request = self.factory.post(self.url_list, {'item_id': self.item.pk, 'quantity': 10})
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(CartItem.objects.get(), self.cart_item)

    def test_unauthorized_update(self):
        url_detail = reverse('cartitems-detail', kwargs={'pk': 1})
        response = self.client.put(url_detail, {'item_id': self.item.pk, 'quantity': 10})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})
        cart_item = CartItem.objects.get()
        self.assertEqual(cart_item.quantity, 5)

    def test_unauthorized_partial_update(self):
        url_detail = reverse('cartitems-detail', kwargs={'pk': 1})
        response = self.client.patch(url_detail, {'quantity': 10})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})
        cart_item = CartItem.objects.get()
        self.assertEqual(cart_item.quantity, 5)

    def test_list(self):
        request = self.factory.get(self.url_list)
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.render()
        self.assertEqual(
            response.data,
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "item":
                            {
                                "id": 1,
                                "title": "title 1",
                                "description": "description 1",
                                "image": "http://testserver/media/test_image.img",
                                "weight": 100,
                                "price": "500.00"
                            },
                        "item_id": 1,
                        "quantity": 5,
                        "price": "500.00",
                        "total_price": "2500.00"}
                ]
            }
        )

    def test_retrieve(self):
        # invalid pk
        url_detail = reverse('cartitems-detail', kwargs={'pk': self.cart_item.pk + 1})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

        # valid pk
        url_detail = reverse('cartitems-detail', kwargs={'pk': self.cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "id": 1,
                "item": {
                    "id": 1,
                    "title": "title 1",
                    "description": "description 1",
                    "image": "http://testserver/media/test_image.img",
                    "weight": 100,
                    "price": "500.00"
                },
                "item_id": 1,
                "quantity": 5,
                "price": "500.00",
                "total_price": "2500.00"
            }
        )

    def test_create(self):
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
        self.assertEqual(CartItem.objects.count(), 1)

        # good data
        cart_item_raw = {
            'item_id': self.item.pk,
            'quantity': 10,
        }
        request = self.factory.post(self.url_list, cart_item_raw)
        force_authenticate(request, self.user)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data,
            {
                "id": 2,
                "item": {
                    "id": 1,
                    "title": "title 1",
                    "description": "description 1",
                    "image": "http://testserver/media/test_image.img",
                    "weight": 100,
                    "price": "500.00"
                },
                "item_id": 1,
                "quantity": 10,
                "price": "500.00",
                "total_price": "5000.00"
            }
        )
        self.assertEqual(CartItem.objects.count(), 2)
        cart_item = CartItem.objects.get(pk=response.data['id'])
        self.assertEqual(cart_item.item_id, self.item.pk)
        self.assertEqual(cart_item.quantity, 10)
        self.assertEqual(cart_item.total_price, self.item.price * 10)

    def test_update(self):
        # empty data
        cart_item_raw = {}
        url_detail = reverse('cartitems-detail', kwargs={'pk': self.cart_item.pk})
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

        # bad pk
        cart_item_raw = {
            'item_id': self.cart_item.item_id,
            'quantity': 10,
        }
        url_detail = reverse('cartitems-detail', kwargs={'pk': self.cart_item.pk + 1})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

        # good data
        cart_item_raw = {
            'item_id': self.cart_item.item_id,
            'quantity': 10,
        }
        url_detail = reverse('cartitems-detail', kwargs={'pk': self.cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "id": 1,
                "item": {
                    "id": 1,
                    "title": "title 1",
                    "description": "description 1",
                    "image": "http://testserver/media/test_image.img",
                    "weight": 100,
                    "price": "500.00"
                },
                "item_id": 1,
                "quantity": 10,
                "price": "500.00",
                "total_price": "5000.00"
            }
        )

        cart_item = CartItem.objects.get(pk=response.data['id'])
        # check db
        self.assertEqual(cart_item.quantity, 10)
        self.assertEqual(float(cart_item.total_price), self.item.price * 10)

        # change price of Item
        self.item.price = 1000
        self.item.save()
        item = Item.objects.get()
        cart_item = CartItem.objects.latest('id')

        cart_item_raw = {
            'item_id': cart_item.item_id,
            'quantity': 20,
        }
        url_detail = reverse('cartitems-detail', kwargs={'pk': cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.put(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "id": 1,
                "item": {
                    "id": 1,
                    "title": "title 1",
                    "description": "description 1",
                    "image": "http://testserver/media/test_image.img",
                    "weight": 100,
                    "price": "1000.00"
                },
                "item_id": 1,
                "quantity": 20,
                "price": "1000.00",
                "total_price": "20000.00"
            }
        )

        cart_item = CartItem.objects.get(pk=response.data['id'])
        # check db
        self.assertEqual(cart_item.quantity, 20)
        self.assertEqual(float(cart_item.price), 1000.)
        self.assertEqual(float(cart_item.total_price), 1000. * 20)

    def test_partial_update(self):
        # empty data
        cart_item_raw = {}
        url_detail = reverse('cartitems-detail', kwargs={'pk': self.cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "id": 1,
                "item": {
                    "id": 1,
                    "title": "title 1",
                    "description": "description 1",
                    "image": "http://testserver/media/test_image.img",
                    "weight": 100,
                    "price": "500.00"
                },
                "item_id": 1,
                "quantity": 5,
                "price": "500.00",
                "total_price": "2500.00"
            },
        )

        # bad pk
        cart_item_raw = {
            'item_id': self.cart_item.item_id,
            'quantity': 10,
        }
        url_detail = reverse('cartitems-detail', kwargs={'pk': self.cart_item.pk + 1})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

        # good data
        cart_item_raw = {
            'quantity': 10,
        }
        url_detail = reverse('cartitems-detail', kwargs={'pk': self.cart_item.pk})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.patch(url_detail, cart_item_raw)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "id": 1,
                "item": {
                    "id": 1,
                    "title": "title 1",
                    "description": "description 1",
                    "image": "http://testserver/media/test_image.img",
                    "weight": 100,
                    "price": "500.00"
                },
                "item_id": 1,
                "quantity": 10,
                "price": "500.00",
                "total_price": "5000.00"
            }
        )

        cart_item = CartItem.objects.get(pk=response.data['id'])
        # check db
        self.assertEqual(cart_item.quantity, 10)
        self.assertEqual(float(cart_item.total_price), self.item.price * 10)

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
        self.item = Item.objects.create(
            title='title 1',
            description='description 1',
            image='test_image.img',
            weight=100,
            price=500,
        )
        self.user = User.objects.create(username='vanya')
        cart = self.user.my_cart
        self.cart_item = CartItem.objects.create(
            item=self.item,
            quantity=5,
            price=self.item.price,
            cart=cart,
        )

    def test_unauthorized(self):
        url_detail = reverse('cartitems-detail', kwargs={'pk': 1})
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})
        self.assertEqual(CartItem.objects.count(), 1)

    def test_destroy(self):
        # invalid pk
        url_detail = reverse('cartitems-detail', kwargs={'pk': self.cart_item.pk + 1})
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})
        self.assertEqual(CartItem.objects.count(), 1)

        # valid pk
        url_detail = reverse('cartitems-detail', kwargs={'pk': self.cart_item.pk})
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
        cls.user = User.objects.create(username='vanya')

    def setUp(self):
        self.view = resolve(self.url).func.cls.as_view(actions={'get': 'list'})

    def test_retrieve_empty_cart(self):
        self.assertEqual(Cart.objects.count(), 0)
        request = self.factory.get(self.url)
        force_authenticate(request, self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Cart.objects.count(), 1)
        cart = Cart.objects.get()
        self.assertEqual(cart.user, self.user)

class CartItemViewSetPaginationTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.url_list = reverse('cartitems-list')
        cls.user = User.objects.create(username='vanya')
        cls.user.set_password('12345678')
        cls.user.save()

    def setUp(self):
        self.view_list = resolve(self.url_list).func.cls.as_view(actions={'get': 'list'})

    def test_pagination(self):
        request = self.factory.get(self.url_list)
        force_authenticate(request, self.user)
        response = self.view_list(request)

        self.assertEqual(
            response.data,
            {
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            }
        )
