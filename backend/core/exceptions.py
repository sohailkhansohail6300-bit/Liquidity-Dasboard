"""One error shape for the whole API: {"error": str, "errors": {field: msg}?, "code": str?, "field": str?}."""
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, Throttled, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class ApiError(Exception):
    def __init__(self, error, status_code=status.HTTP_400_BAD_REQUEST, errors=None, code=None, field=None):
        super().__init__(error)
        self.status_code = status_code
        self.payload = {'error': error}
        if errors:
            self.payload['errors'] = errors
        if code:
            self.payload['code'] = code
        if field:
            self.payload['field'] = field


def _flatten(detail):
    if isinstance(detail, dict):
        for value in detail.values():
            return _flatten(value)
    if isinstance(detail, (list, tuple)):
        return _flatten(detail[0]) if detail else 'Invalid request.'
    return str(detail)


def api_exception_handler(exc, context):
    if isinstance(exc, ApiError):
        return Response(exc.payload, status=exc.status_code)
    response = drf_exception_handler(exc, context)
    if response is None:
        return None
    if isinstance(exc, NotAuthenticated):
        return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    if isinstance(exc, ValidationError):
        data = {'error': _flatten(exc.detail)}
        if isinstance(exc.detail, dict):
            data['errors'] = {k: _flatten(v) for k, v in exc.detail.items()}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, Throttled):
        return Response({'error': 'Too many requests. Please wait a moment and try again.'}, status=response.status_code)
    detail = response.data.get('detail') if isinstance(response.data, dict) else None
    return Response({'error': str(detail) if detail else 'Request failed.'}, status=response.status_code)
