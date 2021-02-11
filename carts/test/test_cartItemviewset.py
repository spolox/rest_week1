from rest_framework.test import APITestCase, APIRequestFactory


class CartItemViewSetListTestCase(APITestCase):
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


class CartItemViewSetCreateTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_unauthorized(self):
        ...

    def test_create(self):
        ...

    def test_validation_data(self):
        ...


class CartItemViewSetDestroyTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        ...

    def test_unauthorized(self):
        ...

    def test_destory(self):
        ...


class CartItemViewSetUpdateTestCase(APITestCase):
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

    def test_validation_data(self):
        ...

