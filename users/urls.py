from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

from .views import UserRegisterCreateAPIVIew, UserCurrentRetrieveUpdateAPIView

urlpatterns_auth = [
    path('login', obtain_auth_token, name='user-login'),
    path('register', UserRegisterCreateAPIVIew.as_view(), name='user-register'),
]

urlpatterns = [
    path('auth/', include(urlpatterns_auth)),
    path('current', UserCurrentRetrieveUpdateAPIView.as_view(), name='user-current'),
]
