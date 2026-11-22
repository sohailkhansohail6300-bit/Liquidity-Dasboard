from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = 'Only administrators can do this.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.kind == 'admin')


class IsNotGuest(BasePermission):
    message = 'Guests have read-only access to this area.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.kind != 'guest')


class IsClientRole(BasePermission):
    """Client and multi-company client users only (not admin, not guest)."""
    message = 'Your account cannot do this.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.kind in ('client', 'colleague'))
