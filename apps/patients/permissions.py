"""
Permissions for Patient records.
Ensures strict ownership-based access control.
"""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow creators of an object to view or edit it.
    """
    message = "You do not have permission to access or modify this patient record."

    def has_object_permission(self, request, view, obj):
        # Read or write permissions are only allowed to the owner of the patient.
        return obj.created_by == request.user
