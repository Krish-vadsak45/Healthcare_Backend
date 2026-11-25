"""
Patient-Doctor Mapping model representing assignment of doctors to patients.
"""
from django.db import models
from django.conf import settings


class PatientDoctorMapping(models.Model):
    """
    Mapping table linking Patients and Doctors.
    Includes unique constraint to prevent duplicate doctor assignments to the same patient.
    """
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='doctor_mappings',
        help_text="Patient receiving care"
    )
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.CASCADE,
        related_name='patient_mappings',
        help_text="Assigned doctor"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_mappings',
        help_text="User who created this assignment"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Clinical notes or reason for assignment"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'healthcare_patient_doctor_mappings'
        verbose_name = 'Patient-Doctor Mapping'
        verbose_name_plural = 'Patient-Doctor Mappings'
        # Prevent assigning the same doctor to the same patient multiple times
        unique_together = ('patient', 'doctor')
        ordering = ['-assigned_at']

    def __str__(self):
        return f"Mapping: Patient '{self.patient.name}' <-> Dr. '{self.doctor.name}' (ID: {self.id})"
