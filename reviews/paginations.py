from rest_framework.pagination import LimitOffsetPagination


class ReviewLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 6
    max_limit = 6
    min_limit = 1
