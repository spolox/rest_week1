from rest_framework.test import APITestCase, APIRequestFactory


class ItemViewSetListTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_ordering_id(self):
        ...

    def test_ordering_price(self):
        ...

    def test_cache(self):
        ...

    def test_pagination(self):
        ...

    def test_list(self):
        ...


class ItemViewSetRetrieveTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_retrive(self):
        ...
