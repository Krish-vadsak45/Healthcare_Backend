"""
URL routes for Patient-Doctor Mapping module.
"""
from django.urls import path
from apps.mappings.views import MappingListCreateView, MappingPatientOrDeleteView

app_name = 'mappings'

urlpatterns = [
    path('', MappingListCreateView.as_view(), name='mapping-list-create'),
    path('<int:id_or_patient_id>/', MappingPatientOrDeleteView.as_view(), name='mapping-patient-or-delete'),
]
