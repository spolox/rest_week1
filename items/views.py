import json

from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .filters import ItemFilter
from .models import Item
from .paginations import ItemPageNumberPagination
from .serializers import ItemSerializer

ITEMS_CACHE_DATA = ''
ITEMS_CACHE_TTL = 60 * 5


class ItemViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    queryset = Item.objects.get_queryset()
    serializer_class = ItemSerializer
    pagination_class = ItemPageNumberPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ItemFilter
    ordering = ['id']
    ordering_fields = ['price']

    def list(self, request, *args, **kwargs):
        cache_response = cache.get(request.build_absolute_uri())
        if cache_response:
            return Response(json.loads(cache_response), status=status.HTTP_200_OK)
        else:
            response = super().list(request, *args, **kwargs)
            cache.set(request.build_absolute_uri(), json.dumps(response.data), ITEMS_CACHE_TTL)
            return response
