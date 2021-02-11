from rest_framework.test import APITestCase, APIRequestFactory


class ReviewViewSetListTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_pagination(self):
        ...

    def test_ordering_published_at(self):
        ...

    def test_list(self):
        ...


class ReviewViewSetCreateTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_unauthorized(self):
        ...

    def test_create(self):
        ...

    def test_validation(self):
        ...
