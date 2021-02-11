from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import UserSerializer


class UserRegisterCreateAPIView(CreateAPIView):
    serializer_class = UserSerializer


class UserCurrentRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
