from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from .filters import ItemFilter
from .models import Item
from .paginations import ItemPageNumberPagination
from .serializers import ItemSerializer


class ItemViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Item.objects.get_queryset()
    serializer_class = ItemSerializer
    pagination_class = ItemPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ItemFilter
    ordering = ['id']
    ordering_fields = ['price']
