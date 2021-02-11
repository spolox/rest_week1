from rest_framework import mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from .models import Review
from .paginations import ReviewLimitOffsetPagination
from .serializers import ReviewSerializer


class ReviewViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    pagination_class = ReviewLimitOffsetPagination
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        permissions = []
        if self.action == 'create':
            permissions.append(IsAuthenticated)

        return [permission() for permission in permissions]

    def get_queryset(self):
        queryset = Review.objects.filter(status=Review.StatusChoices.PUBLISHED)
        return queryset.all().order_by('-published_at')
