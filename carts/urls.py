from django.urls import path

from .views import CartViewSet, CartItemViewSet

urlpatterns = [
    path(r'', CartViewSet.as_view({'get': 'retrieve'}), name='cart'),
    path(
        r'items',
        CartItemViewSet.as_view(
            {
                'get': 'list',
                'post': 'create',
            },
            name='items',
        ),
    ),
    path(
        r'items/<int:pk>',
        CartItemViewSet.as_view(
            {
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy',
            },
            name='items-detail',
        ),
    ),
]
