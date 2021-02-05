from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CartViewSet, CartItemViewSet

router = DefaultRouter()
router.register('items', CartItemViewSet, basename='cart_items')

urlpatterns = [
    path(r'', CartViewSet.as_view({'get': 'retrieve'}), name='cart'),
]

urlpatterns += router.urls
