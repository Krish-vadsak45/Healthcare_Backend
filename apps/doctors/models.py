"""
Doctor model representing healthcare professionals.
"""
from django.db import models
from django.conf import settings


class Doctor(models.Model):
    """
    Doctor model representing medical practitioners.
    Accessible platform-wide to authenticated users.
    """
    name = models.CharField(max_length=255, db_index=True)
    specialization = models.CharField(max_length=255, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(max_length=20)
    years_of_experience = models.PositiveIntegerField(default=0)
    hospital_affiliation = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_doctors',
        help_text="User who registered this doctor into the system"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'healthcare_doctors'
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'
        ordering = ['-created_at']

    def __str__(self):
        return f"Dr. {self.name} - {self.specialization} (ID: {self.id})"
