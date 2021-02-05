from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from .models import Cart, CartItem
from .paginations import CartItemLimitOffsetPagination
from .serializers import CartSerializer, CartItemSerializer


class CartViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Cart, user=self.request.user)


class CartItemViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                      mixins.DestroyModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    pagination_class = CartItemLimitOffsetPagination
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = get_object_or_404(Cart, user=self.request.user)
        return queryset.cart_items.all()

    def get_object(self):
        queryset = get_object_or_404(Cart, user=self.request.user)
        return get_object_or_404(queryset.cart_items, pk=self.kwargs['pk'])
