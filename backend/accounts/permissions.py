from rest_framework.permissions import BasePermission
from rest_framework.views import APIView

from common.api import ApiError

from .access import get_access


class IsActiveUser(BasePermission):
    """Signed in, with an account that has been set up (or a seeded demo user while demo mode is on)."""
    message = 'Sign in to continue.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.can_use_portal)


class RolePermission(BasePermission):
    """Restricts a view to the roles in ``view.allowed_roles``. Roles are resolved on the server."""
    message = 'This page is not part of your access.'

    def has_permission(self, request, view):
        roles = getattr(view, 'allowed_roles', None)
        if not roles:
            return True
        return get_access(request).role in roles


class PortalAPIView(APIView):
    """Base class for signed-in endpoints."""
    permission_classes = [IsActiveUser, RolePermission]
    allowed_roles = None

    @property
    def access(self):
        return get_access(self.request)


def company_for(request, company_id):
    """Return the Company only if the signed-in user may see it.

    Unknown ids and companies the user cannot see get the *same* 403, so the API never confirms
    which company ids exist (tenant isolation / no IDOR).
    """
    from companies.models import Company
    access = get_access(request)
    if company_id not in access.allowed:
        raise ApiError('You do not have access to that company.', 403, 'forbidden')
    company = Company.objects.filter(pk=company_id).first()
    if company is None:
        raise ApiError('You do not have access to that company.', 403, 'forbidden')
    return company
