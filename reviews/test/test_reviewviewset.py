from copy import deepcopy

from django.urls import reverse, resolve
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from reviews.models import Review
from reviews.serializers import ReviewSerializer
from users.models import User


class ReviewViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.url = reverse('reviews-list')

    def setUp(self):
        self.view = resolve(self.url).func.cls.as_view(actions={'get': 'list', 'post': 'create'})
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
        for i in range(10):
            Review.objects.create(
                text=f'{i}',
                author=self.user,
                status=Review.StatusChoices.PUBLISHED,
            )
        Review.objects.create(text='11', author=self.user)
        Review.objects.create(text='12', author=self.user, status=Review.StatusChoices.HIDDEN)

    def test_db(self):
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Review.objects.count(), 12)
        user = User.objects.get(pk=self.user.pk)
        user_raw = deepcopy(self.user_raw)
        user_raw['username'] = 'vanya'
        self.assertEqual(user_raw['email'], user.email)
        self.assertEqual(user_raw['first_name'], user.first_name)
        self.assertEqual(user_raw['last_name'], user.last_name)
        self.assertEqual(user_raw['middle_name'], user.middle_name)
        self.assertEqual(user_raw['phone'], user.phone)
        self.assertEqual(user_raw['address'], user.address)
        self.assertTrue(user.check_password('12345678'))

        reviews = Review.objects.all()
        texts = [f'{i}' for i in range(10)]
        for review in reviews:
            self.assertEqual(review.author, user)
            if review.text == '11':
                self.assertEqual(review.status, Review.StatusChoices.NEW)
                continue
            if review.text == '12':
                self.assertEqual(review.status, Review.StatusChoices.HIDDEN)
                continue
            self.assertEqual(review.status, Review.StatusChoices.PUBLISHED)
            self.assertIn(review.text, texts)
            texts.remove(review.text)
        self.assertEqual(len(texts), 0)

    def test_unauthorized_create(self):
        request = self.factory.post(self.url)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_pagination(self):
        request = self.factory.get(self.url)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertIsNone(response.data['previous'])
        self.assertIn('/api/v1/reviews/?limit=6&offset=6', response.data['next'])
        self.assertEqual(len(response.data['results']), 6)
        request = self.factory.get(response.data['next'])
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 10)
        self.assertIsNone(response.data['next'])
        self.assertIn('/api/v1/reviews/?limit=6', response.data['previous'])
        self.assertEqual(len(response.data['results']), 4)

        # check max limit
        request = self.factory.get(self.url+'?limit=7')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 6)

        request = self.factory.get(self.url + '?limit=5')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

        # check min limit
        request = self.factory.get(self.url + '?limit=0')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 6)

        # with offset
        request = self.factory.get(self.url + '?limit=6&offset=3')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('/api/v1/reviews/?limit=6&offset=9', response.data['next'])
        self.assertIn('/api/v1/reviews/?limit=6', response.data['previous'])
        self.assertEqual(len(response.data['results']), 6)

        request = self.factory.get(self.url + '?limit=6&offset=5')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['next'])
        self.assertIn('/api/v1/reviews/?limit=6', response.data['previous'])
        self.assertEqual(len(response.data['results']), 5)

    def test_ordering_published_at(self):
        request = self.factory.get(self.url)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reviews = response.data['results']
        is_ordering_published_at = all(
            parse_datetime(reviews[i]['published_at']) >= parse_datetime(reviews[i+1]['published_at'])
            for i in range(len(reviews) - 1)
        )
        self.assertTrue(is_ordering_published_at)
        reviews = reviews[::-1]
        is_not_ordering_published_at = all(
            parse_datetime(reviews[i]['published_at']) >= parse_datetime(reviews[i + 1]['published_at'])
            for i in range(len(reviews) - 1)
        )
        self.assertFalse(is_not_ordering_published_at)

    def test_list(self):
        request = self.factory.get(self.url)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_reviews = response.data['results']
        request = self.factory.get(response.data['next'])
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_reviews += response.data['results']

        reviews = list(Review.objects.all().values('id', 'status'))

        for response_review in response_reviews:
            review = Review.objects.get(pk=response_review['id'])
            review_data = ReviewSerializer(review).data
            self.assertEqual(review_data, response_review)
            # remove from reviews one object
            reviews = [review for review in reviews if review['id'] != response_review['id']]

        # here must be 2 reviews with status new and hidden, they don't show in response
        self.assertEqual(len(reviews), 2)
        self.assertIn(reviews[0]['status'], ['new', 'hidden'])
        self.assertIn(reviews[1]['status'], ['new', 'hidden'])

    def test_create(self):
        review_raw = {}
        request = self.factory.post(self.url, review_raw)
        force_authenticate(request, self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"text": ["This field is required."]})
        review_raw = {'text': '1234'}
        request = self.factory.post(self.url, review_raw)
        force_authenticate(request, self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Review.objects.count(), 13)

        review = Review.objects.get(pk=response.data['id'])
        review_data = ReviewSerializer(review).data
        # check database
        self.assertEqual(review.author, self.user)
        self.assertEqual(review.text, review_raw['text'])
        self.assertEqual(review.status, Review.StatusChoices.NEW)
        self.assertEqual(review.created_at, parse_datetime(response.data['created_at']))
        self.assertIsNone(review.published_at)

        # check response
        self.assertEqual(response.data, review_data)
