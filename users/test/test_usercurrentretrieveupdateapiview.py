from rest_framework.test import APITestCase, APIRequestFactory


class UserRegisterCreateAPIViewCreateTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_create(self):
        ...
