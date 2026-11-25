"""
Automated unit and integration tests for Patient-Doctor Mapping APIs and Edge Cases.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.mappings.models import PatientDoctorMapping


class MappingAPITests(APITestCase):
    """
    Test suite for Patient-Doctor Mapping assignments, duplicate prevention, and patient doctor lookups.
    """
    def setUp(self):
        self.user_a = User.objects.create_user(
            name='User A',
            email='user.a@hospital.org',
            password='Password123!'
        )
        self.user_b = User.objects.create_user(
            name='User B',
            email='user.b@hospital.org',
            password='PasswordB123!'
        )

        self.patient_a = Patient.objects.create(
            created_by=self.user_a,
            name='Patient A',
            age=35,
            gender='Female',
            contact_number='1234567890'
        )

        self.patient_b = Patient.objects.create(
            created_by=self.user_b,
            name='Patient B',
            age=40,
            gender='Male',
            contact_number='9876543210'
        )

        self.doctor_1 = Doctor.objects.create(
            created_by=self.user_a,
            name='Dr. Strange',
            specialization='Neurosurgeon',
            email='strange@hospital.org',
            phone_number='1122334455'
        )

        self.doctor_2 = Doctor.objects.create(
            created_by=self.user_a,
            name='Dr. Watson',
            specialization='General Practitioner',
            email='watson@hospital.org',
            phone_number='9988776655'
        )

        self.mapping_list_create_url = reverse('mappings:mapping-list-create')

    def test_assign_doctor_to_patient_success(self):
        """Verify authenticated user can assign a doctor to their patient."""
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'patient': self.patient_a.id,
            'doctor': self.doctor_1.id,
            'notes': 'Referred for neuro evaluation'
        }
        response = self.client.post(self.mapping_list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['patient']['id'], self.patient_a.id)
        self.assertEqual(response.data['data']['doctor']['id'], self.doctor_1.id)
        self.assertTrue(PatientDoctorMapping.objects.filter(patient=self.patient_a, doctor=self.doctor_1).exists())

    def test_assign_doctor_duplicate_fails(self):
        """Verify assigning the same doctor to the same patient again fails."""
        PatientDoctorMapping.objects.create(
            patient=self.patient_a,
            doctor=self.doctor_1,
            assigned_by=self.user_a
        )

        self.client.force_authenticate(user=self.user_a)
        payload = {
            'patient': self.patient_a.id,
            'doctor': self.doctor_1.id
        }
        response = self.client.post(self.mapping_list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_assign_nonexistent_patient_fails(self):
        """Edge Case: Assigning to a patient ID that does not exist must fail."""
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'patient': 999999,
            'doctor': self.doctor_1.id
        }
        response = self.client.post(self.mapping_list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_assign_nonexistent_doctor_fails(self):
        """Edge Case: Assigning a doctor ID that does not exist must fail."""
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'patient': self.patient_a.id,
            'doctor': 999999
        }
        response = self.client.post(self.mapping_list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_assign_missing_fields_fails(self):
        """Edge Case: Missing patient and doctor fields returns 400."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(self.mapping_list_create_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_cannot_assign_doctor_to_another_users_patient(self):
        """Verify a user cannot assign doctors to a patient they do not own."""
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'patient': self.patient_b.id,
            'doctor': self.doctor_1.id
        }
        response = self.client.post(self.mapping_list_create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_get_all_doctors_assigned_to_specific_patient(self):
        """Verify GET /api/mappings/<patient_id>/ returns all doctors mapped to the patient."""
        PatientDoctorMapping.objects.create(patient=self.patient_a, doctor=self.doctor_1, assigned_by=self.user_a)
        PatientDoctorMapping.objects.create(patient=self.patient_a, doctor=self.doctor_2, assigned_by=self.user_a)

        self.client.force_authenticate(user=self.user_a)
        url = reverse('mappings:mapping-patient-or-delete', kwargs={'id_or_patient_id': self.patient_a.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['assigned_doctors_count'], 2)
        doctor_ids = [d['doctor']['id'] for d in response.data['doctors']]
        self.assertIn(self.doctor_1.id, doctor_ids)
        self.assertIn(self.doctor_2.id, doctor_ids)

    def test_get_doctors_for_nonexistent_patient_fails(self):
        """Edge Case: Requesting doctors for a nonexistent patient returns 404."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('mappings:mapping-patient-or-delete', kwargs={'id_or_patient_id': 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])

    def test_get_doctors_for_another_users_patient_forbidden(self):
        """Edge Case: Requesting doctors for another user's patient returns 404 (isolation)."""
        self.client.force_authenticate(user=self.user_a)
        url = reverse('mappings:mapping-patient-or-delete', kwargs={'id_or_patient_id': self.patient_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])

    def test_delete_mapping_by_id(self):
        """Verify DELETE /api/mappings/<id>/ removes a doctor from a patient."""
        mapping = PatientDoctorMapping.objects.create(
            patient=self.patient_a,
            doctor=self.doctor_1,
            assigned_by=self.user_a
        )

        self.client.force_authenticate(user=self.user_a)
        delete_url = reverse('mappings:mapping-patient-or-delete', kwargs={'id_or_patient_id': mapping.id})
        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PatientDoctorMapping.objects.filter(id=mapping.id).exists())

    def test_delete_nonexistent_mapping_returns_404(self):
        """Edge Case: Deleting a mapping that doesn't exist returns 404."""
        self.client.force_authenticate(user=self.user_a)
        delete_url = reverse('mappings:mapping-patient-or-delete', kwargs={'id_or_patient_id': 999999})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])

    def test_delete_mapping_unauthorized_user_forbidden(self):
        """Verify another user cannot delete mappings for a patient they do not own."""
        mapping = PatientDoctorMapping.objects.create(
            patient=self.patient_a,
            doctor=self.doctor_1,
            assigned_by=self.user_a
        )

        self.client.force_authenticate(user=self.user_b)
        delete_url = reverse('mappings:mapping-patient-or-delete', kwargs={'id_or_patient_id': mapping.id})
        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertTrue(PatientDoctorMapping.objects.filter(id=mapping.id).exists())
