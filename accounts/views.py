from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView

from .serializers import ProfileStatsSerializer, UserTokenObtainPairSerializer


class UserTokenObtainPairView(TokenObtainPairView):
    serializer_class = UserTokenObtainPairSerializer


class LogoutView(TokenBlacklistView):
    permission_classes = (IsAuthenticated,)


class ProfileStatsView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileStatsSerializer

    def get_object(self):
        return self.request.user
