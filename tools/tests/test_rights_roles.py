from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase

from core.models.openimis_graphql_test_case import BaseTestContext
from core.test_helpers import (
    create_monitoring_evaluation_role,
    create_right_only_user,
    create_role_user,
)
from location.test_helpers import create_basic_test_locations


class RegisterRightsTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_basic_test_locations()
        cls.cases = [
            ("registers_locations_perms", "registers/download_locations", "rloc"),
            ("registers_health_facilities_perms", "registers/download_healthfacilities", "rhf"),
            ("registers_diagnoses_perms", "registers/download_diagnoses", "rdia"),
            ("registers_items_perms", "registers/download_items", "ritm"),
            ("registers_services_perms", "registers/download_services", "rsvc"),
        ]

    def _headers(self, user):
        token = BaseTestContext(user=user).get_jwt()
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _url(self, path):
        return f"/{settings.SITE_ROOT()}tools/{path}"

    def test_register_downloads_allowed_and_denied(self):
        for perm, path, suffix in self.cases:
            with self.subTest(perm=perm):
                allowed = create_right_only_user(f"r_{suffix}", [perm])
                denied = create_right_only_user(f"n_{suffix}", [])
                response = self.client.get(self._url(path), **self._headers(allowed))
                self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
                response_no = self.client.get(self._url(path), **self._headers(denied))
                self.assertIn(
                    response_no.status_code,
                    (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
                    response_no.content,
                )


class RegisterRoleTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_basic_test_locations()
        cls.me = create_role_user("reg_me", create_monitoring_evaluation_role())

    def _headers(self, user):
        token = BaseTestContext(user=user).get_jwt()
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_monitoring_evaluation_can_download_registers(self):
        paths = [
            "registers/download_locations",
            "registers/download_healthfacilities",
            "registers/download_diagnoses",
            "registers/download_items",
            "registers/download_services",
        ]
        for path in paths:
            with self.subTest(path=path):
                url = f"/{settings.SITE_ROOT()}tools/{path}"
                response = self.client.get(url, **self._headers(self.me))
                self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
