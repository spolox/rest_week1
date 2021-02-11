from rest_framework.test import APITestCase, APIRequestFactory


class UserCurrentRetrieveUpdateAPIViewRetrieveTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_unauthorized(self):
        ...

    def test_retrieve(self):
        ...

    def test_validation(self):
        ...


class UserCurrentRetrieveUpdateAPIViewUpdateTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_unauthorized(self):
        ...

    def test_update(self):
        ...

    def test_partial_update(self):
        ...

    def test_validation(self):
        ...
