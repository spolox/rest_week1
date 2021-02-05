from rest_framework.pagination import PageNumberPagination


class ItemPageNumberPagination(PageNumberPagination):
    page_size = 6
