from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView


def enforce_csrf(request):
    """Same CSRF check DRF's SessionAuthentication runs, applied to public (unauthenticated) POST endpoints."""
    check = CSRFCheck(lambda r: None)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise PermissionDenied('CSRF Failed: %s' % reason)


class PublicAPIView(APIView):
    """No authentication, CSRF enforced on unsafe methods (protects login/sign-up against cross-site forgery)."""
    authentication_classes = []
    permission_classes = []

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            enforce_csrf(request)
