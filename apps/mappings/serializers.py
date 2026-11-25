"""
Serializers for Patient-Doctor Mapping operations.
"""
from rest_framework import serializers
from apps.mappings.models import PatientDoctorMapping
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.doctors.serializers import DoctorSummarySerializer


class PatientSummarySerializer(serializers.ModelSerializer):
    """
    Lightweight summary serializer for patient in mapping representations.
    """
    class Meta:
        model = Patient
        fields = ('id', 'name', 'age', 'gender', 'contact_number')
        read_only_fields = fields


class PatientDoctorMappingCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new patient-doctor mapping.
    Validates patient ownership and uniqueness.
    """
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())

    class Meta:
        model = PatientDoctorMapping
        fields = ('id', 'patient', 'doctor', 'notes', 'assigned_at')
        read_only_fields = ('id', 'assigned_at')

    def validate(self, attrs):
        patient = attrs.get('patient')
        doctor = attrs.get('doctor')
        request = self.context.get('request')

        # Verify strict patient ownership: Authenticated user must own the patient record
        if request and request.user and patient.created_by != request.user:
            raise serializers.ValidationError({
                "patient": "You can only assign doctors to patients that you have created."
            })

        # Check for existing duplicate assignment
        if PatientDoctorMapping.objects.filter(patient=patient, doctor=doctor).exists():
            raise serializers.ValidationError(
                f"Doctor '{doctor.name}' is already assigned to Patient '{patient.name}'."
            )

        return attrs


class PatientDoctorMappingDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed view of patient-doctor mappings.
    Includes nested patient and doctor representations.
    """
    patient = PatientSummarySerializer(read_only=True)
    doctor = DoctorSummarySerializer(read_only=True)
    assigned_by_email = serializers.EmailField(source='assigned_by.email', read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = (
            'id',
            'patient',
            'doctor',
            'notes',
            'assigned_by_email',
            'assigned_at'
        )
        read_only_fields = fields


class AssignedDoctorRecordSerializer(serializers.ModelSerializer):
    """
    Serializer representing an assigned doctor for a specific patient.
    """
    mapping_id = serializers.IntegerField(source='id', read_only=True)
    doctor = DoctorSummarySerializer(read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = ('mapping_id', 'doctor', 'notes', 'assigned_at')
        read_only_fields = fields
