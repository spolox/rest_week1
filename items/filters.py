from django_filters.rest_framework import FilterSet

from .models import Item


class ItemFilter(FilterSet):
    class Meta:
        model = Item
        fields = {
            'price': ['gte', 'lte', 'gt', 'lt'],
            'weight': ['gte', 'lte', 'gt', 'lt'],
        }