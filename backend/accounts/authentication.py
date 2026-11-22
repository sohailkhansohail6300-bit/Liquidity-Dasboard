from rest_framework.authentication import SessionAuthentication


class CsrfEnforcedSessionAuthentication(SessionAuthentication):
    """Session authentication that enforces CSRF on *every* unsafe request.

    DRF's stock class only checks CSRF for authenticated users, which would leave login and the
    public sign-up / access-request endpoints open to cross-site form posts.
    """

    def authenticate(self, request):
        user = getattr(request._request, 'user', None)
        self.enforce_csrf(request)
        if not user or not user.is_active:
            return None
        return (user, None)

    def authenticate_header(self, request):
        # Makes DRF answer 401 (not 403) for anonymous requests.
        return 'Session'
