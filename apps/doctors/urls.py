"""
URL routes for Doctors module.
"""
from django.urls import path
from apps.doctors.views import DoctorListCreateView, DoctorDetailView

app_name = 'doctors'

urlpatterns = [
    path('', DoctorListCreateView.as_view(), name='doctor-list-create'),
    path('<int:id>/', DoctorDetailView.as_view(), name='doctor-detail'),
]
