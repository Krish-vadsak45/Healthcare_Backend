"""
Views for Doctor Management.
"""
import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.doctors.models import Doctor
from apps.doctors.serializers import DoctorSerializer

logger = logging.getLogger(__name__)


class DoctorListCreateView(generics.ListCreateAPIView):
    """
    POST: Add a new doctor (Authenticated users only).
    GET: Retrieve all doctors in the directory.
    """
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]
    queryset = Doctor.objects.all().select_related('created_by')

    def perform_create(self, serializer):
        doctor = serializer.save(created_by=self.request.user)
        logger.info(
            "Doctor created successfully [Doctor ID: %s, Name: Dr. %s] by user: %s",
            doctor.id, doctor.name, self.request.user.email
        )

    @extend_schema(
        tags=['Doctors'],
        summary='Retrieve all doctors',
        description='Fetches a paginated list of all doctors registered in the system.',
        responses={200: DoctorSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=['Doctors'],
        summary='Add a new doctor',
        description='Registers a new doctor record in the system.',
        request=DoctorSerializer,
        responses={
            201: OpenApiResponse(response=DoctorSerializer, description='Doctor created successfully.'),
            400: OpenApiResponse(description='Validation error.')
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Get details of a specific doctor.
    PUT/PATCH: Update doctor details.
    DELETE: Delete a doctor record.
    """
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]
    queryset = Doctor.objects.all().select_related('created_by')
    lookup_field = 'id'

    def perform_update(self, serializer):
        doctor = serializer.save()
        logger.info(
            "Doctor updated successfully [Doctor ID: %s, Name: Dr. %s] by user: %s",
            doctor.id, doctor.name, self.request.user.email
        )

    def perform_destroy(self, instance):
        doctor_id = instance.id
        doctor_name = instance.name
        instance.delete()
        logger.info(
            "Doctor deleted successfully [Doctor ID: %s, Name: Dr. %s] by user: %s",
            doctor_id, doctor_name, self.request.user.email
        )

    @extend_schema(
        tags=['Doctors'],
        summary='Get details of a specific doctor',
        description='Retrieves the detailed record of a specific doctor by ID.',
        responses={
            200: DoctorSerializer,
            404: OpenApiResponse(description='Doctor not found.')
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        tags=['Doctors'],
        summary='Update doctor details',
        description='Updates all fields of an existing doctor record.',
        request=DoctorSerializer,
        responses={
            200: DoctorSerializer,
            400: OpenApiResponse(description='Validation error.'),
            404: OpenApiResponse(description='Doctor not found.')
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        tags=['Doctors'],
        summary='Partially update doctor details',
        description='Updates specific fields of an existing doctor record.',
        request=DoctorSerializer,
        responses={
            200: DoctorSerializer,
            400: OpenApiResponse(description='Validation error.'),
            404: OpenApiResponse(description='Doctor not found.')
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        tags=['Doctors'],
        summary='Delete a doctor record',
        description='Removes a doctor record from the system.',
        responses={
            204: OpenApiResponse(description='Doctor deleted successfully.'),
            404: OpenApiResponse(description='Doctor not found.')
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
