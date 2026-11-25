"""
Automated unit and integration tests for Patients API and Edge Cases.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.patients.models import Patient


class PatientAPITests(APITestCase):
    """
    Test suite for Patient CRUD endpoints, boundary validations, and strict ownership isolation.
    """
    def setUp(self):
        self.user_a = User.objects.create_user(
            name='User A',
            email='user.a@hospital.org',
            password='PasswordA123!'
        )
        self.user_b = User.objects.create_user(
            name='User B',
            email='user.b@hospital.org',
            password='PasswordB123!'
        )

        self.list_create_url = reverse('patients:patient-list-create')

        self.patient_a_data = {
            'name': 'John Doe',
            'age': 45,
            'gender': 'Male',
            'contact_number': '+1-555-0199',
            'email': 'john.doe@example.com',
            'address': '123 Pine St, Cityville',
            'medical_history': 'Hypertension, seasonal allergies'
        }

    def test_create_patient_authenticated(self):
        """Verify authenticated user can create patient and ownership is automatically assigned."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.list_create_url, self.patient_a_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'John Doe')
        self.assertEqual(response.data['created_by_email'], self.user_a.email)

        patient = Patient.objects.get(id=response.data['id'])
        self.assertEqual(patient.created_by, self.user_a)

    def test_create_patient_unauthenticated_fails(self):
        """Verify unauthenticated requests to create patient are rejected with 401."""
        response = self.client.post(self.list_create_url, self.patient_a_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'not_authenticated')

    def test_create_patient_negative_age_fails(self):
        """Edge Case: Age below 0 must fail validation with friendly message."""
        self.client.force_authenticate(user=self.user_a)
        data = self.patient_a_data.copy()
        data['age'] = -5
        response = self.client.post(self.list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('Age', response.data['error']['message'])

    def test_create_patient_unrealistically_high_age_fails(self):
        """Edge Case: Age > 150 must fail validation."""
        self.client.force_authenticate(user=self.user_a)
        data = self.patient_a_data.copy()
        data['age'] = 250
        response = self.client.post(self.list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_patient_invalid_contact_number_fails(self):
        """Edge Case: Contact number under 7 chars must fail."""
        self.client.force_authenticate(user=self.user_a)
        data = self.patient_a_data.copy()
        data['contact_number'] = '123'
        response = self.client.post(self.list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_patient_invalid_gender_choice_fails(self):
        """Edge Case: Invalid gender choice must fail."""
        self.client.force_authenticate(user=self.user_a)
        data = self.patient_a_data.copy()
        data['gender'] = 'InvalidGender'
        response = self.client.post(self.list_create_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_patient_missing_required_fields_fails(self):
        """Edge Case: Missing name, age, gender must return 400."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.list_create_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('name', response.data['error']['details'])

    def test_strict_ownership_patient_list_isolation(self):
        """
        Verify GET /api/patients/ retrieves strictly patients created by the authenticated user.
        User A creates 2 patients, User B creates 1 patient.
        """
        Patient.objects.create(created_by=self.user_a, name='Patient A1', age=30, gender='Female', contact_number='1234567890')
        Patient.objects.create(created_by=self.user_a, name='Patient A2', age=32, gender='Male', contact_number='1234567891')
        Patient.objects.create(created_by=self.user_b, name='Patient B1', age=40, gender='Other', contact_number='9876543210')

        # Authenticate as User A
        self.client.force_authenticate(user=self.user_a)
        res_a = self.client.get(self.list_create_url)
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        self.assertEqual(res_a.data['count'], 2)
        patient_names_a = [item['name'] for item in res_a.data['results']]
        self.assertIn('Patient A1', patient_names_a)
        self.assertIn('Patient A2', patient_names_a)
        self.assertNotIn('Patient B1', patient_names_a)

        # Authenticate as User B
        self.client.force_authenticate(user=self.user_b)
        res_b = self.client.get(self.list_create_url)
        self.assertEqual(res_b.status_code, status.HTTP_200_OK)
        self.assertEqual(res_b.data['count'], 1)
        patient_names_b = [item['name'] for item in res_b.data['results']]
        self.assertIn('Patient B1', patient_names_b)
        self.assertNotIn('Patient A1', patient_names_b)

    def test_strict_ownership_patient_detail_access(self):
        """
        Verify that a user cannot view, update, or delete another user's patient.
        """
        patient_a = Patient.objects.create(
            created_by=self.user_a,
            name='Private Patient A',
            age=50,
            gender='Male',
            contact_number='1234567890'
        )
        detail_url = reverse('patients:patient-detail', kwargs={'id': patient_a.id})

        # User A can access their own patient
        self.client.force_authenticate(user=self.user_a)
        res_owner = self.client.get(detail_url)
        self.assertEqual(res_owner.status_code, status.HTTP_200_OK)

        # User B attempts to access User A's patient -> Expect 404 (isolation)
        self.client.force_authenticate(user=self.user_b)
        res_other = self.client.get(detail_url)
        self.assertEqual(res_other.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(res_other.data['success'])

        # User B attempts to update User A's patient -> Expect 404
        res_update = self.client.put(detail_url, {'name': 'Hacked', 'age': 20, 'gender': 'Male', 'contact_number': '1111111111'})
        self.assertEqual(res_update.status_code, status.HTTP_404_NOT_FOUND)

        # User B attempts to delete User A's patient -> Expect 404
        res_delete = self.client.delete(detail_url)
        self.assertEqual(res_delete.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Patient.objects.filter(id=patient_a.id).exists())

    def test_get_nonexistent_patient_returns_404(self):
        """Edge Case: Requesting nonexistent patient returns friendly 404."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('patients:patient-detail', kwargs={'id': 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'not_found')

    def test_update_and_delete_patient_by_owner(self):
        """Verify owner can successfully update and delete patient."""
        patient = Patient.objects.create(
            created_by=self.user_a,
            name='Editable Patient',
            age=25,
            gender='Female',
            contact_number='1234567890'
        )
        detail_url = reverse('patients:patient-detail', kwargs={'id': patient.id})

        self.client.force_authenticate(user=self.user_a)

        # Partial update
        patch_res = self.client.patch(detail_url, {'name': 'Updated Patient Name'}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data['name'], 'Updated Patient Name')

        # Delete
        delete_res = self.client.delete(detail_url)
        self.assertEqual(delete_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Patient.objects.filter(id=patient.id).exists())
