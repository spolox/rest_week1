from django.urls import path

from .views import item_detail

urlpatterns = [
    path('<int:pk>/', item_detail, name='item-detail'),
]
