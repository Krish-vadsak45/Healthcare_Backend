"""
Views for Patient Management with strict ownership-based access control.
"""
import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.patients.models import Patient
from apps.patients.serializers import PatientSerializer
from apps.patients.permissions import IsOwner

logger = logging.getLogger(__name__)


class PatientListCreateView(generics.ListCreateAPIView):
    """
    POST: Add a new patient (Authenticated users only, auto-sets created_by).
    GET: Retrieve all patients created by the authenticated user.
    """
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Enforce strict data isolation: Return only patients created by the authenticated user.
        """
        user = self.request.user
        logger.debug("Fetching patients created by user: %s (ID: %s)", user.email, user.id)
        return Patient.objects.filter(created_by=user).select_related('created_by')

    def perform_create(self, serializer):
        """
        Automatically bind the patient record to the currently authenticated user.
        """
        patient = serializer.save(created_by=self.request.user)
        logger.info(
            "Patient created successfully [Patient ID: %s, Name: %s] by user: %s",
            patient.id, patient.name, self.request.user.email
        )

    @extend_schema(
        tags=['Patients'],
        summary='Retrieve all patients created by current user',
        description='Fetches a paginated list of patients created by the authenticated user.',
        responses={200: PatientSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=['Patients'],
        summary='Add a new patient',
        description='Creates a new patient record owned by the authenticated user.',
        request=PatientSerializer,
        responses={
            201: OpenApiResponse(response=PatientSerializer, description='Patient created successfully.'),
            400: OpenApiResponse(description='Validation error.')
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Get details of a specific patient (Owner only).
    PUT/PATCH: Update patient details (Owner only).
    DELETE: Delete a patient record (Owner only).
    """
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    lookup_field = 'id'

    def get_queryset(self):
        """
        Scope queryset strictly to records owned by the authenticated user.
        If a user tries to access another user's patient ID, it yields a 404 Not Found.
        """
        return Patient.objects.filter(created_by=self.request.user).select_related('created_by')

    def perform_update(self, serializer):
        patient = serializer.save()
        logger.info(
            "Patient updated successfully [Patient ID: %s, Name: %s] by user: %s",
            patient.id, patient.name, self.request.user.email
        )

    def perform_destroy(self, instance):
        patient_id = instance.id
        patient_name = instance.name
        instance.delete()
        logger.info(
            "Patient deleted successfully [Patient ID: %s, Name: %s] by user: %s",
            patient_id, patient_name, self.request.user.email
        )

    @extend_schema(
        tags=['Patients'],
        summary='Get details of a specific patient',
        description='Retrieves the detailed record of a patient owned by the authenticated user.',
        responses={
            200: PatientSerializer,
            404: OpenApiResponse(description='Patient not found or unauthorized.')
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=['Patients'],
        summary='Update patient details',
        description='Updates a patient record owned by the authenticated user.',
        request=PatientSerializer,
        responses={
            200: PatientSerializer,
            400: OpenApiResponse(description='Validation error.'),
            404: OpenApiResponse(description='Patient not found or unauthorized.')
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        tags=['Patients'],
        summary='Partially update patient details',
        description='Partially updates specific fields of a patient record owned by the authenticated user.',
        request=PatientSerializer,
        responses={
            200: PatientSerializer,
            400: OpenApiResponse(description='Validation error.'),
            404: OpenApiResponse(description='Patient not found or unauthorized.')
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        tags=['Patients'],
        summary='Delete a patient record',
        description='Deletes a patient record owned by the authenticated user.',
        responses={
            204: OpenApiResponse(description='Patient deleted successfully.'),
            404: OpenApiResponse(description='Patient not found or unauthorized.')
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
