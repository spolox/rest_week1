from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from items.models import Item


@api_view(http_method_names=['GET'])
def item_detail(request, pk):
    response = get_object_or_404(Item, pk=pk)
    return Response(response.as_json())
