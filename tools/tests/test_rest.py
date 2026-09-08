
from core.test_helpers import create_test_interactive_user
from rest_framework import status
from rest_framework.test import APITestCase
from graphql_jwt.shortcuts import get_token
from django.conf import settings
import os
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models.openimis_graphql_test_case import BaseTestContext as DummyContext


class ReportAPITests(APITestCase):

    admin_user = None
    admin_token = None
    dir_path = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = create_test_interactive_user(username="testLocationAdmin")
        cls.admin_token = get_token(cls.admin_user, DummyContext(user=cls.admin_user))
        cls.dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    def test_import_item_json(self):
        URL = f'/{settings.SITE_ROOT()}tools/imports/items?file_format=json'
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        with open(os.path.join(self.dir_path, 'tests/item_example.json'), 'rb') as f:
            file_content = f.read()
            uploaded_file = SimpleUploadedFile("service_example.json", file_content, content_type="application/json")
            response = self.client.post(URL, {'file': uploaded_file}, format='multipart', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_export_item_xls(self):
        URL = f'/{settings.SITE_ROOT()}tools/exports/items?file_format=xls'
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        response = self.client.get(URL, format='json', **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_import_service_json(self):
        URL = f'/{settings.SITE_ROOT()}tools/imports/services?file_format=json'
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        with open(os.path.join(self.dir_path, 'tests/service_example.json'), 'rb') as f:
            file_content = f.read()
            uploaded_file = SimpleUploadedFile("service_example.json", file_content, content_type="application/json")
            response = self.client.post(URL, {'file': uploaded_file}, format='multipart', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_export_service_xls(self):
        URL = f'/{settings.SITE_ROOT()}tools/exports/services?file_format=xls'
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.admin_token}"}
        response = self.client.get(URL, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

# todo expand tests
