from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import LogoutView, ProfileStatsView, UserTokenObtainPairView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", UserTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/logout/", LogoutView.as_view(), name="logout"),
    path("api/profile/stats/", ProfileStatsView.as_view(), name="profile_stats"),
]
