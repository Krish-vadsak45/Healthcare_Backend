"""
Views for Patient-Doctor Mapping APIs:
- POST /api/mappings/ - Assign a doctor to a patient
- GET /api/mappings/ - Retrieve all patient-doctor mappings
- GET /api/mappings/<patient_id>/ - Get all doctors assigned to a specific patient
- DELETE /api/mappings/<id>/ - Remove a doctor from a patient
"""
import logging
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.mappings.models import PatientDoctorMapping
from apps.patients.models import Patient
from apps.mappings.serializers import (
    PatientDoctorMappingCreateSerializer,
    PatientDoctorMappingDetailSerializer,
    AssignedDoctorRecordSerializer
)

logger = logging.getLogger(__name__)


class MappingListCreateView(APIView):
    """
    POST /api/mappings/ - Assign a doctor to a patient.
    GET /api/mappings/ - Retrieve all patient-doctor mappings.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='mappings_list_all',
        tags=['Mappings'],
        summary='Retrieve all patient-doctor mappings',
        description='Fetches all patient-doctor assignments with full nested patient and doctor details.',
        responses={200: PatientDoctorMappingDetailSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        # Retrieve all mappings (or scoped to user's patients if desired)
        mappings = PatientDoctorMapping.objects.select_related('patient', 'doctor', 'assigned_by').all()
        serializer = PatientDoctorMappingDetailSerializer(mappings, many=True)
        return Response({
            'success': True,
            'count': mappings.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Mappings'],
        summary='Assign a doctor to a patient',
        description='Creates an association between a patient and a doctor.',
        request=PatientDoctorMappingCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=PatientDoctorMappingDetailSerializer,
                description='Doctor successfully assigned to patient.'
            ),
            400: OpenApiResponse(description='Validation error or duplicate assignment.')
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = PatientDoctorMappingCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        mapping = serializer.save(assigned_by=request.user)

        logger.info(
            "Doctor assigned to patient [Mapping ID: %s, Patient ID: %s, Doctor ID: %s] by user: %s",
            mapping.id, mapping.patient.id, mapping.doctor.id, request.user.email
        )
        return Response({
            'success': True,
            'message': 'Doctor successfully assigned to patient.',
            'data': PatientDoctorMappingDetailSerializer(mapping).data
        }, status=status.HTTP_201_CREATED)


class MappingPatientOrDeleteView(APIView):
    """
    Unified view handling:
    - GET /api/mappings/<patient_id>/ - Get all doctors assigned to a specific patient.
    - DELETE /api/mappings/<id>/ - Remove a doctor from a patient (delete mapping by mapping ID).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='mappings_get_by_patient',
        tags=['Mappings'],
        summary='Get all doctors assigned to a specific patient',
        description='Retrieves the list of all doctors assigned to the specified patient ID.',
        responses={
            200: AssignedDoctorRecordSerializer(many=True),
            404: OpenApiResponse(description='Patient not found or unauthorized.')
        }
    )
    def get(self, request, id_or_patient_id, *args, **kwargs):
        """
        Interprets id_or_patient_id as patient_id.
        Validates patient ownership (authenticated user must own the patient).
        """
        patient = get_object_or_404(Patient, id=id_or_patient_id, created_by=request.user)

        mappings = PatientDoctorMapping.objects.filter(patient=patient).select_related('doctor')
        serializer = AssignedDoctorRecordSerializer(mappings, many=True)

        logger.info(
            "Retrieved assigned doctors for Patient ID: %s [Count: %d] by user: %s",
            patient.id, mappings.count(), request.user.email
        )
        return Response({
            'success': True,
            'patient_id': patient.id,
            'patient_name': patient.name,
            'assigned_doctors_count': mappings.count(),
            'doctors': serializer.data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id='mappings_remove_doctor_assignment',
        tags=['Mappings'],
        summary='Remove a doctor from a patient (Delete mapping)',
        description='Deletes a patient-doctor mapping record by mapping ID.',
        responses={
            204: OpenApiResponse(description='Mapping successfully removed.'),
            404: OpenApiResponse(description='Mapping record not found.')
        }
    )
    def delete(self, request, id_or_patient_id, *args, **kwargs):
        """
        Interprets id_or_patient_id as mapping ID.
        Locates and deletes the mapping record.
        """
        mapping = get_object_or_404(PatientDoctorMapping, id=id_or_patient_id)
        
        # Verify user owns the patient in this mapping
        if mapping.patient.created_by != request.user:
            raise PermissionDenied("You do not have permission to delete mappings for this patient.")

        mapping_id = mapping.id
        patient_name = mapping.patient.name
        doctor_name = mapping.doctor.name

        mapping.delete()
        logger.info(
            "Mapping removed [Mapping ID: %s, Patient: %s, Doctor: Dr. %s] by user: %s",
            mapping_id, patient_name, doctor_name, request.user.email
        )
        return Response({
            'success': True,
            'message': f"Doctor '{doctor_name}' unassigned from Patient '{patient_name}'."
        }, status=status.HTTP_204_NO_CONTENT)
