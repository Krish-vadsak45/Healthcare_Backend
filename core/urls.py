"""
Main URL Configuration for Healthcare Backend.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


def health_check(request):
    """Simple health check endpoint returning API status."""
    return JsonResponse({
        "status": "healthy",
        "service": "Healthcare Backend API",
        "version": "1.0.0",
        "documentation": "/api/docs/"
    })


urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),

    # Health Check
    path('', health_check, name='health-check'),
    path('api/health/', health_check, name='api-health-check'),

    # API Domain Routes
    path('api/auth/', include('apps.authentication.urls', namespace='authentication')),
    path('api/patients/', include('apps.patients.urls', namespace='patients')),
    path('api/doctors/', include('apps.doctors.urls', namespace='doctors')),
    path('api/mappings/', include('apps.mappings.urls', namespace='mappings')),

    # OpenAPI 3 / Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
