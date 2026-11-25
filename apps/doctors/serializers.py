"""
Serializers for Doctor records.
"""
from rest_framework import serializers
from apps.doctors.models import Doctor


class DoctorSerializer(serializers.ModelSerializer):
    """
    Serializer for Doctor CRUD operations.
    """
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = Doctor
        fields = (
            'id',
            'name',
            'specialization',
            'email',
            'phone_number',
            'years_of_experience',
            'hospital_affiliation',
            'created_by',
            'created_by_name',
            'created_by_email',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def validate_email(self, value):
        normalized = value.strip().lower()
        # Ensure email uniqueness, excluding current instance during update
        query = Doctor.objects.filter(email__iexact=normalized)
        if self.instance:
            query = query.exclude(id=self.instance.id)
        if query.exists():
            raise serializers.ValidationError("A doctor with this email address already exists.")
        return normalized

    def validate_years_of_experience(self, value):
        if value < 0 or value > 80:
            raise serializers.ValidationError("Years of experience must be between 0 and 80.")
        return value

    def validate_phone_number(self, value):
        cleaned = value.strip()
        if len(cleaned) < 7 or len(cleaned) > 20:
            raise serializers.ValidationError("Phone number must be between 7 and 20 characters.")
        return cleaned


class DoctorSummarySerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for nested doctor representations (e.g., in mappings).
    """
    class Meta:
        model = Doctor
        fields = ('id', 'name', 'specialization', 'email', 'phone_number')
        read_only_fields = fields
