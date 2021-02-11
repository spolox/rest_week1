from rest_framework.test import APITestCase, APIRequestFactory


class CartViewSetRetrieveTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_unauthorized(self):
        ...

    def test_retrive(self):
        ...
