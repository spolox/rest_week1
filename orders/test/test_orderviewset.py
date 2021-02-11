from rest_framework.test import APITestCase, APIRequestFactory


class OrderViewSetListTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_unauthorized(self):
        ...

    def test_pagination(self):
        ...

    def test_list(self):
        ...


class OrderViewSetRetrieveTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_unauthorized(self):
        ...

    def test_retrive(self):
        ...


class OrderViewSetCreateTestCase(APITestCase):
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


class OrderViewSetUpdateTestCase(APITestCase):
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
