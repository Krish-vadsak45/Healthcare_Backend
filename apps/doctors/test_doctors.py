"""
Automated unit and integration tests for Doctors API and Edge Cases.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.doctors.models import Doctor


class DoctorAPITests(APITestCase):
    """
    Test suite for Doctor CRUD operations, edge cases, and validations.
    """
    def setUp(self):
        self.user = User.objects.create_user(
            name='Hospital Admin',
            email='admin@hospital.org',
            password='Password123!'
        )
        self.list_create_url = reverse('doctors:doctor-list-create')

        self.doctor_data = {
            'name': 'Gregory House',
            'specialization': 'Diagnostic Medicine',
            'email': 'house@princetonplainsboro.org',
            'phone_number': '+1-609-555-0100',
            'years_of_experience': 20,
            'hospital_affiliation': 'Princeton-Plainsboro Teaching Hospital'
        }

    def test_create_doctor_authenticated(self):
        """Verify authenticated user can register a new doctor."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_create_url, self.doctor_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], self.doctor_data['name'])
        self.assertEqual(response.data['specialization'], self.doctor_data['specialization'])
        self.assertEqual(response.data['created_by_email'], self.user.email)
        self.assertTrue(Doctor.objects.filter(email=self.doctor_data['email']).exists())

    def test_create_doctor_unauthenticated_fails(self):
        """Verify unauthenticated requests cannot create doctor records."""
        response = self.client.post(self.list_create_url, self.doctor_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])

    def test_create_doctor_negative_experience_fails(self):
        """Edge Case: Negative years of experience must fail validation."""
        self.client.force_authenticate(user=self.user)
        data = self.doctor_data.copy()
        data['years_of_experience'] = -3
        response = self.client.post(self.list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Years of experience', response.data['error']['message'])

    def test_create_doctor_excessive_experience_fails(self):
        """Edge Case: Experience > 80 years must fail validation."""
        self.client.force_authenticate(user=self.user)
        data = self.doctor_data.copy()
        data['years_of_experience'] = 99
        response = self.client.post(self.list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_doctor_invalid_phone_number_fails(self):
        """Edge Case: Phone number < 7 chars must fail."""
        self.client.force_authenticate(user=self.user)
        data = self.doctor_data.copy()
        data['phone_number'] = '123'
        response = self.client.post(self.list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_doctor_missing_required_fields_fails(self):
        """Edge Case: Missing name, email, specialization must return 400."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_create_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('name', response.data['error']['details'])
        self.assertIn('email', response.data['error']['details'])

    def test_list_all_doctors(self):
        """Verify all authenticated users can retrieve the doctor directory."""
        Doctor.objects.create(created_by=self.user, **self.doctor_data)
        Doctor.objects.create(
            created_by=self.user,
            name='James Wilson',
            specialization='Oncology',
            email='wilson@princetonplainsboro.org',
            phone_number='+1-609-555-0101',
            years_of_experience=18
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_duplicate_doctor_email_fails(self):
        """Verify registering doctor with existing email returns 400 Bad Request."""
        Doctor.objects.create(created_by=self.user, **self.doctor_data)

        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_create_url, self.doctor_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_get_nonexistent_doctor_returns_404(self):
        """Edge Case: Nonexistent doctor ID returns friendly 404."""
        self.client.force_authenticate(user=self.user)
        url = reverse('doctors:doctor-detail', kwargs={'id': 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])

    def test_update_doctor_duplicate_email_conflict(self):
        """Edge Case: Updating doctor A's email to doctor B's email must fail."""
        doc1 = Doctor.objects.create(created_by=self.user, **self.doctor_data)
        doc2 = Doctor.objects.create(
            created_by=self.user,
            name='Doctor Two',
            specialization='Pediatrics',
            email='doctor.two@hospital.org',
            phone_number='1234567890'
        )

        self.client.force_authenticate(user=self.user)
        detail_url = reverse('doctors:doctor-detail', kwargs={'id': doc2.id})
        # Attempt to set doc2's email to doc1's email
        response = self.client.patch(detail_url, {'email': doc1.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_update_and_delete_doctor(self):
        """Verify doctor details can be updated and deleted."""
        doctor = Doctor.objects.create(created_by=self.user, **self.doctor_data)
        detail_url = reverse('doctors:doctor-detail', kwargs={'id': doctor.id})

        self.client.force_authenticate(user=self.user)

        patch_res = self.client.patch(detail_url, {'years_of_experience': 22}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['years_of_experience'], 22)

        del_res = self.client.delete(detail_url)
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Doctor.objects.filter(id=doctor.id).exists())
