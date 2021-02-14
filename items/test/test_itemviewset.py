import pathlib

from django.conf import settings
from django.core.cache import cache
from django.urls import reverse, resolve
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from items.models import Item
from items.serializers import ItemSerializer


class ItemViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url_list = reverse('item-list')
        cls.factory = APIRequestFactory()
        for i in range(1, 11):
            Item.objects.create(
                title=f'title {i}',
                description=f'description {i}',
                image='test_image.img',
                weight=i * 10,
                price=i * 100,
            )

    def setUp(self):
        self.view_list = resolve(self.url_list).func.cls.as_view(actions={'get': 'list'})

    def test_db(self):
        self.assertEqual(Item.objects.count(), 10)
        items = Item.objects.all().order_by('weight')
        index = 1
        for item in items:
            self.assertEqual(item.title, f'title {index}')
            self.assertEqual(item.description, f'description {index}')
            self.assertEqual(item.image.url, pathlib.Path(settings.MEDIA_URL, 'test_image.img').as_posix())
            self.assertEqual(item.weight, index * 10)
            self.assertEqual(item.price, index * 100)
            index += 1

    def test_ordering_id(self):
        request = self.factory.get(self.url_list)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['results']
        is_ordering_id = all(
            items[i]['id'] < items[i+1]['id'] for i in range(len(items) - 1)
        )
        self.assertTrue(is_ordering_id)
        items = items[::-1]
        is_not_ordering_id = all(
            items[i]['id'] < items[i + 1]['id'] for i in range(len(items) - 1)
        )
        self.assertFalse(is_not_ordering_id)

    def test_ordering_price(self):
        # test ordering price
        request = self.factory.get(self.url_list + '?ordering=price')
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['results']
        is_ordering_id = all(
            float(items[i]['price']) <= float(items[i + 1]['price']) for i in range(len(items) - 1)
        )
        self.assertTrue(is_ordering_id)

        # test ordering -price
        request = self.factory.get(self.url_list + '?ordering=-price')
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['results']
        is_ordering_id = all(
            float(items[i]['price']) >= float(items[i + 1]['price']) for i in range(len(items) - 1)
        )
        self.assertTrue(is_ordering_id)

    def test_filter_price(self):
        # test price__gt and price__lt
        request = self.factory.get(self.url_list + '?price__gt=100&price__lt=300')
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['results']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['price'], '200.00')
        # test price__gte and price__lte
        request = self.factory.get(self.url_list + '?price__gte=100&price__lte=300')
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['results']
        self.assertEqual(len(items), 3)
        for item in items:
            self.assertIn(item['price'], ['100.00', '200.00', '300.00'])

    def test_filter_weight(self):
        # test weight__gt and weight__lt
        request = self.factory.get(self.url_list + '?weight__gt=10&weight__lt=30')
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['results']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['weight'], 20)
        # test weight__gte and weight__lte
        request = self.factory.get(self.url_list + '?weight__gte=10&weight__lte=30')
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['results']
        self.assertEqual(len(items), 3)
        for item in items:
            self.assertIn(item['weight'], [10, 20, 30])

    def test_pagination(self):
        request = self.factory.get(self.url_list)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertIsNone(response.data['previous'])
        self.assertIn('/api/v1/items/?page=2', response.data['next'])
        self.assertEqual(len(response.data['results']), 6)
        request = self.factory.get(response.data['next'])
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertIsNone(response.data['next'])
        self.assertIn('/api/v1/items/', response.data['previous'])
        self.assertEqual(len(response.data['results']), 4)

    def test_list(self):
        request = self.factory.get(self.url_list)
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_items = response.data['results']
        request = self.factory.get(response.data['next'])
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_items += response.data['results']

        self.assertEqual(len(response_items), 10)

        for response_item in response_items:
            item_data = ItemSerializer(Item.objects.get(pk=response_item['id'])).data
            self.assertEqual(response_item['title'], item_data['title'])
            self.assertEqual(response_item['description'], item_data['description'])
            self.assertIn(item_data['image'], response_item['image'])
            self.assertEqual(response_item['weight'], item_data['weight'])
            self.assertEqual(response_item['price'], item_data['price'])

    def test_retrieve(self):
        url_detail = reverse('item-detail', kwargs={'pk': 11})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail': 'Not found.'})

        url_detail = reverse('item-detail', kwargs={'pk': 1})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item_data = ItemSerializer(Item.objects.get(pk=response.data['id'])).data
        self.assertEqual(response.data['title'], item_data['title'])
        self.assertEqual(response.data['description'], item_data['description'])
        self.assertIn(item_data['image'], response.data['image'])
        self.assertEqual(response.data['weight'], item_data['weight'])
        self.assertEqual(response.data['price'], item_data['price'])


class ItemViewSetCacheTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url_list = reverse('item-list')
        cls.factory = APIRequestFactory()

    def setUp(self):
        self.view_list = resolve(self.url_list).func.cls.as_view(actions={'get': 'list'})
        for i in range(1, 11):
            Item.objects.create(
                title=f'title {i}',
                description=f'description {i}',
                image='test_image.img',
                weight=i * 10,
                price=i * 100,
            )

    def test_cache(self):
        request = self.factory.get(self.url_list)
        self.assertIsNone(cache.get(request.build_absolute_uri()))
        response = self.view_list(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(request.build_absolute_uri()))
        Item.objects.create(title='2', description='2', image='test_image.img', weight=10, price=100)
        self.assertIsNone(cache.get(request.build_absolute_uri()))
