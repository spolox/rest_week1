from django.shortcuts import get_object_or_404
from rest_framework import mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from .models import Order
from .paginations import OrderLimitOffsetPagination
from .serializers import OrderSerializer, OrderRetrieveUpdateSerializer


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                   mixins.CreateModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderLimitOffsetPagination
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('retrieve', 'update', 'partial_update'):
            return OrderRetrieveUpdateSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = Order.objects.filter(recipient=self.request.user)
        return queryset.all()

    def get_object(self):
        queryset = Order.objects.filter(recipient=self.request.user)
        return get_object_or_404(queryset, pk=self.kwargs['pk'])
