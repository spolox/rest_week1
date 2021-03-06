from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from .views import UserCurrentRetrieveUpdateAPIView, UserRegisterCreateAPIVIew

urlpatterns_auth = [
    path('login', obtain_auth_token, name='login'),
    path('register', UserRegisterCreateAPIVIew.as_view(), name='register'),
]

urlpatterns = [
    path('auth/', include(urlpatterns_auth)),
    path('current', UserCurrentRetrieveUpdateAPIView.as_view(), name='current'),
]
