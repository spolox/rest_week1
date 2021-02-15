from rest_framework.routers import DefaultRouter

from .views import ReviewViewSet

router = DefaultRouter()
router.register(r'', ReviewViewSet, basename='reviews')

urlpatterns = []

urlpatterns += router.urls
