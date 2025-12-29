from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

class CompanyTests(TestCase):
    def test_get_companies(self):
        client = APIClient()
        response = client.get('/api/companies/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
