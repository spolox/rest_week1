from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from items.models import Item


@api_view(http_method_names=['GET'])
def item_detail(request, pk):
    try:
        response = Item.objects.filter(pk=pk).get()
    except ObjectDoesNotExist:
        response = None

    if response:
        return Response(response.as_json())
    else:
        return Response(status=status.HTTP_404_NOT_FOUND)
