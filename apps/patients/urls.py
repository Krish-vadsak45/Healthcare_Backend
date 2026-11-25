"""
URL routes for Patients module.
"""
from django.urls import path
from apps.patients.views import PatientListCreateView, PatientDetailView

app_name = 'patients'

urlpatterns = [
    path('', PatientListCreateView.as_view(), name='patient-list-create'),
    path('<int:id>/', PatientDetailView.as_view(), name='patient-detail'),
]
