"""Shared API plumbing: a consistent error envelope and small helpers.

Every error response has the same shape::

    {"detail": "Human readable message", "code": "machine_code", "errors": {"field": "message"}}

``errors`` is only present for field-level validation problems.
"""
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (APIException, AuthenticationFailed, NotAuthenticated, PermissionDenied,
                                       Throttled, ValidationError)
from rest_framework.views import exception_handler as drf_exception_handler


class ApiError(APIException):
    """Raise from services/views to return a clean, consistent error."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'error'

    def __init__(self, detail, status_code=None, code=None, errors=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail, code or self.default_code)
        self.errors = errors or {}


def _first_message(value):
    if isinstance(value, (list, tuple)):
        return _first_message(value[0]) if value else ''
    if isinstance(value, dict):
        return _first_message(next(iter(value.values()), ''))
    return str(value)


def api_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = APIException('Not found.')
        exc.status_code = status.HTTP_404_NOT_FOUND
        exc.default_code = 'not_found'
    response = drf_exception_handler(exc, context)
    if response is None:
        return None     # unexpected errors fall through to Django's 500 handling (no stack trace leaks in prod)

    code = getattr(exc, 'default_code', 'error')
    errors = {}
    if isinstance(exc, ApiError):
        detail = _first_message(exc.detail)
        errors = exc.errors
        code = exc.get_codes() if isinstance(exc.get_codes(), str) else code
    elif isinstance(exc, ValidationError):
        data = exc.detail
        if isinstance(data, dict):
            errors = {k: _first_message(v) for k, v in data.items() if k != 'non_field_errors'}
            detail = _first_message(data.get('non_field_errors')) if data.get('non_field_errors') else (
                'Please fix the highlighted fields.')
        else:
            detail = _first_message(data)
        code = 'validation_error'
    elif isinstance(exc, NotAuthenticated):
        detail, code = 'Sign in to continue.', 'not_authenticated'
    elif isinstance(exc, AuthenticationFailed):
        detail, code = _first_message(exc.detail), 'authentication_failed'
    elif isinstance(exc, PermissionDenied):
        detail, code = _first_message(exc.detail), 'forbidden'
    elif isinstance(exc, Throttled):
        detail, code = 'Too many attempts. Please wait a moment and try again.', 'throttled'
    else:
        detail = _first_message(getattr(exc, 'detail', 'Request failed.'))

    body = {'detail': detail, 'code': code}
    if errors:
        body['errors'] = errors
    response.data = body
    return response


def field_errors(errors, message='Please fix the highlighted fields.', code='validation_error'):
    """Raise a 400 with per-field messages (the shape the forms in the UI expect)."""
    raise ApiError(message, 400, code, errors)
