from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import authenticate
from django.core.management import call_command
from django.test import TestCase
from django.utils.dateparse import parse_datetime
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .admin import CustomUserAdmin
from .models import CustomUser


class CustomUserTests(TestCase):
    def test_user_defaults_and_optional_profile_fields(self):
        user = CustomUser.objects.create_user(
            email="client@example.com",
            username="client",
            password="secure-test-password",
        )

        self.assertEqual(user.role, CustomUser.Role.CLIENT)
        self.assertFalse(user.is_verified)
        self.assertEqual(user.bio, "")
        self.assertIsNone(user.birth_date)

    def test_superuser_manager_sets_required_permissions(self):
        user = CustomUser.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="secure-test-password",
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_createsuperuser_management_command(self):
        with patch.dict("os.environ", {"DJANGO_SUPERUSER_PASSWORD": "secure-test-password"}):
            call_command(
                "createsuperuser",
                email="command-admin@example.com",
                username="command-admin",
                interactive=False,
                verbosity=0,
            )

        user = CustomUser.objects.get(email="command-admin@example.com")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("secure-test-password"))

    def test_email_authentication_and_admin_user_creation(self):
        admin_user = CustomUser.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="secure-admin-password",
        )
        self.assertEqual(
            authenticate(email=admin_user.email, password="secure-admin-password"),
            admin_user,
        )

        self.client.force_login(admin_user)
        response = self.client.post(
            reverse("admin:accounts_customuser_add"),
            {
                "email": "new-client@example.com",
                "username": "new-client",
                "password1": "Strong!ClientPass902",
                "password2": "Strong!ClientPass902",
                "role": CustomUser.Role.CLIENT,
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        new_user = CustomUser.objects.get(email="new-client@example.com")
        self.assertEqual(new_user.role, CustomUser.Role.CLIENT)
        self.assertFalse(new_user.is_staff)

    def test_admin_lists_and_filters_expected_fields(self):
        model_admin = CustomUserAdmin(CustomUser, admin.site)

        self.assertEqual(
            model_admin.get_list_display(None),
            ("email", "role", "is_verified", "is_active"),
        )
        self.assertEqual(
            model_admin.get_list_filter(None),
            ("role", "is_verified"),
        )
        self.assertEqual(
            model_admin.get_search_fields(None),
            ("email", "username"),
        )

    def test_admin_add_form_exposes_email_and_username(self):
        self.assertEqual(
            CustomUserAdmin.add_form.base_fields.keys(),
            {"email", "username", "password1", "password2"},
        )


class JWTApiTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="jwt-user@example.com",
            username="jwt-user",
            password="secure-test-password",
            role=CustomUser.Role.USER,
        )
        self.client = APIClient()

    def test_login_returns_user_details_and_tokens(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": self.user.email, "password": "secure-test-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(
            {
                key: response.data[key]
                for key in ("id", "email", "username", "role")
            },
            {
                "id": self.user.pk,
                "email": self.user.email,
                "username": self.user.username,
                "role": self.user.role,
            },
        )
        access = AccessToken(response.data["access"])
        refresh = RefreshToken(response.data["refresh"])
        self.assertEqual(access["exp"] - access["iat"], 15 * 60)
        self.assertEqual(refresh["exp"] - refresh["iat"], 7 * 24 * 60 * 60)

    def test_logout_blacklists_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.force_authenticate(user=self.user)

        logout_response = self.client.post(
            reverse("logout"),
            {"refresh": str(refresh)},
            format="json",
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_stats_requires_authentication_and_returns_user_stats(self):
        url = reverse("profile_stats")
        self.assertEqual(
            self.client.get(url).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["role"], self.user.role)
        self.assertFalse(response.data["is_staff"])
        self.assertEqual(
            parse_datetime(response.data["date_joined"]),
            self.user.date_joined,
        )
