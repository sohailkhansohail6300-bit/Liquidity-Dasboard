from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Sign in with an email address (case-insensitive). Pending invitations have no usable password."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = (username or kwargs.get('email') or '').strip()
        if not email or password is None:
            return None
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            User().set_password(password)   # constant-ish timing for unknown addresses
            return None
        if user.status != User.Status.ACTIVE or not user.has_usable_password():
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
