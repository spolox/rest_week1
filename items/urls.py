from django.urls import path

from items.views import item_detail

urlpatterns = [
    path('<int:pk>/', item_detail, name='item-detail'),
]
