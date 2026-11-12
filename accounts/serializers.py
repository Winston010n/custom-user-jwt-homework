from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import CustomUser


class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update(
            {
                "id": self.user.pk,
                "email": self.user.email,
                "username": self.user.username,
                "role": self.user.role,
            }
        )
        return data


class ProfileStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("email", "role", "is_staff", "date_joined")
