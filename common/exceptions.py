"""
Enhanced user-friendly DRF exception handler.
Transforms all API exceptions, validation errors, auth failures,
and database integrity errors into clear, human-readable JSON responses.
"""
import logging
from django.db import IntegrityError
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError,
    NotAuthenticated,
    AuthenticationFailed,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
    UnsupportedMediaType
)

logger = logging.getLogger(__name__)


def _format_error_detail(detail):
    """
    Recursively format error detail into clean, readable strings or dicts.
    Flattens single-item lists for clean presentation.
    """
    if isinstance(detail, list):
        if len(detail) == 1:
            return _format_error_detail(detail[0])
        return [_format_error_detail(item) for item in detail]
    elif isinstance(detail, dict):
        return {key: _format_error_detail(val) for key, val in detail.items()}
    return str(detail)


def _extract_primary_message(details, exc):
    """
    Extract a concise, user-friendly primary error message from details.
    """
    if isinstance(details, dict):
        # 1. Check for standard 'detail'
        if 'detail' in details:
            return str(details['detail'])

        # 2. Check for 'non_field_errors'
        if 'non_field_errors' in details:
            nfe = details['non_field_errors']
            return str(nfe[0] if isinstance(nfe, list) else nfe)

        # 3. Extract the first field validation error and format like "Email: A user with this email already exists."
        first_key = next(iter(details))
        first_val = details[first_key]
        if isinstance(first_val, list) and len(first_val) > 0:
            val_str = str(first_val[0])
        else:
            val_str = str(first_val)

        field_name = first_key.replace('_', ' ').capitalize()
        return f"{field_name}: {val_str}"

    elif isinstance(details, list) and len(details) > 0:
        return str(details[0])

    # Fallback to exception message
    return str(exc) if str(exc) else "An unexpected error occurred while processing your request."


def custom_exception_handler(exc, context):
    """
    Global exception handler that standardizes all error responses into:
    {
        "success": False,
        "error": {
            "type": "ValidationError",
            "code": "invalid_input",
            "message": "Human-readable friendly message",
            "details": {...}
        }
    }
    """
    # First, handle database integrity errors before DRF default
    if isinstance(exc, IntegrityError):
        logger.warning("Database IntegrityError: %s", str(exc))
        return Response(
            {
                "success": False,
                "error": {
                    "type": "ConflictError",
                    "code": "unique_constraint_violation",
                    "message": "A database conflict occurred. A record with these unique details already exists.",
                    "details": {"database": str(exc)}
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Let DRF handle standard REST framework exceptions
    response = exception_handler(exc, context)

    view = context.get('view')
    view_name = view.__class__.__name__ if view else 'UnknownView'
    request = context.get('request')
    method = request.method if request else 'UNKNOWN'

    if response is not None:
        raw_data = response.data
        error_type = exc.__class__.__name__
        error_code = getattr(exc, 'default_code', 'error')

        # Friendly defaults for common HTTP errors
        if isinstance(exc, NotAuthenticated):
            message = "Authentication credentials were not provided. Please include a valid Bearer token in the Authorization header."
            error_code = "not_authenticated"
        elif isinstance(exc, AuthenticationFailed):
            message = "Authentication failed. The provided token or credentials are invalid or expired."
            error_code = "authentication_failed"
        elif isinstance(exc, (PermissionDenied, DjangoPermissionDenied)):
            message = "You do not have permission to access or modify this resource."
            error_code = "permission_denied"
        elif isinstance(exc, (NotFound, Http404)):
            message = "The requested resource could not be found or you do not have permission to view it."
            error_code = "not_found"
        elif isinstance(exc, MethodNotAllowed):
            message = f"The {method} method is not allowed on this endpoint."
            error_code = "method_not_allowed"
        elif isinstance(exc, UnsupportedMediaType):
            message = "Unsupported media type. Please provide 'application/json' in the Content-Type header."
            error_code = "unsupported_media_type"
        else:
            # Extract most descriptive field message
            message = _extract_primary_message(raw_data, exc)

        formatted_details = _format_error_detail(raw_data)

        custom_response_data = {
            "success": False,
            "error": {
                "type": error_type,
                "code": error_code,
                "message": message,
                "details": formatted_details
            }
        }

        logger.warning(
            "API Error handled in %s [%s] -> %s (Status: %d)",
            view_name,
            method,
            message,
            response.status_code
        )
        response.data = custom_response_data
        return response

    # Unhandled 500 exceptions
    logger.exception("Unhandled server exception in %s [%s]: %s", view_name, method, str(exc))
    return Response(
        {
            "success": False,
            "error": {
                "type": "InternalServerError",
                "code": "server_error",
                "message": "An unexpected server error occurred. Our team has been notified. Please try again later.",
                "details": None
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
