"""
Patient model with ownership relationship to the user who created the record.
"""
from django.db import models
from django.conf import settings


class Patient(models.Model):
    """
    Patient model representing individuals receiving medical care.
    Scoped strictly by creator user for data privacy and security.
    """
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=255, db_index=True)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True, help_text="Past conditions, allergies, or notes")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patients',
        help_text="The authenticated user who created and owns this patient record"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'healthcare_patients'
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (Age: {self.age}, ID: {self.id})"
