"""
Automated unit and integration tests for Authentication APIs and Edge Cases.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User


class AuthenticationAPITests(APITestCase):
    """
    Test suite for user registration, login, JWT token issuance, and edge cases.
    """
    def setUp(self):
        self.register_url = reverse('authentication:register')
        self.login_url = reverse('authentication:login')
        self.token_refresh_url = reverse('authentication:token_refresh')

        self.user_data = {
            'name': 'Dr. Alice Smith',
            'email': 'alice.smith@hospital.org',
            'password': 'StrongPassword123!'
        }

    def test_register_user_success(self):
        """Verify successful user registration returns 201 and user details."""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], self.user_data['email'].lower())
        self.assertEqual(response.data['data']['name'], self.user_data['name'])
        self.assertNotIn('password', response.data['data'])
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())

    def test_register_duplicate_email_fails(self):
        """Verify registration with duplicate email returns 400 Bad Request."""
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('email', response.data['error']['details'])
        self.assertIn('Email', response.data['error']['message'])

    def test_register_short_password_fails(self):
        """Verify registration with short password fails Django password validation."""
        invalid_data = {
            'name': 'Short Pass',
            'email': 'short@hospital.org',
            'password': '123'
        }
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('password', response.data['error']['details'])

    def test_register_missing_required_fields_fails(self):
        """Verify registration with missing fields returns 400 with user-friendly errors."""
        response = self.client.post(self.register_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('email', response.data['error']['details'])
        self.assertIn('password', response.data['error']['details'])
        self.assertIn('name', response.data['error']['details'])

    def test_register_invalid_email_format_fails(self):
        """Verify registration with invalid email format is rejected."""
        payload = {
            'name': 'Invalid Email',
            'email': 'not-an-email',
            'password': 'Password123!'
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('email', response.data['error']['details'])

    def test_login_success_returns_jwt_tokens(self):
        """Verify login with correct credentials returns 200 and access/refresh tokens."""
        User.objects.create_user(**self.user_data)
        login_payload = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['email'], self.user_data['email'].lower())

    def test_login_case_insensitive_email(self):
        """Verify user can log in with uppercase email."""
        User.objects.create_user(**self.user_data)
        login_payload = {
            'email': self.user_data['email'].upper(),
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_login_wrong_password_fails(self):
        """Verify login with invalid password returns 400 Bad Request."""
        User.objects.create_user(**self.user_data)
        wrong_payload = {
            'email': self.user_data['email'],
            'password': 'WrongPassword999!'
        }
        response = self.client.post(self.login_url, wrong_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_nonexistent_email_fails(self):
        """Verify login with unregistered email returns 400 Bad Request."""
        payload = {
            'email': 'nonexistent@hospital.org',
            'password': 'Password123!'
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_fields_fails(self):
        """Verify login without email or password returns 400."""
        response = self.client.post(self.login_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_disabled_user_fails(self):
        """Verify inactive/disabled user cannot log in."""
        user = User.objects.create_user(**self.user_data)
        user.is_active = False
        user.save()

        response = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_jwt_token_refresh(self):
        """Verify that refresh token can successfully obtain a new access token."""
        User.objects.create_user(**self.user_data)
        login_res = self.client.post(self.login_url, {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }, format='json')
        refresh_token = login_res.data['tokens']['refresh']

        refresh_res = self.client.post(self.token_refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_res.data)

    def test_jwt_token_refresh_invalid_token_fails(self):
        """Verify invalid or malformed refresh token returns 401 Unauthorized."""
        response = self.client.post(self.token_refresh_url, {'refresh': 'invalid.token.structure'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
