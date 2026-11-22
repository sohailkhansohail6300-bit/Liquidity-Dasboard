from rest_framework.authentication import SessionAuthentication


class SessionAuth(SessionAuthentication):
    """Django session authentication with two changes:

    * CSRF is enforced for *every* unsafe request, including anonymous ones (login, sign-up, access requests),
      which closes login-CSRF.
    * Unauthenticated requests answer 401 (DRF would answer 403 for plain SessionAuthentication).
    """

    def authenticate(self, request):
        user = getattr(request._request, 'user', None)
        self.enforce_csrf(request)
        if not user or not user.is_active:
            return None
        return (user, None)

    def authenticate_header(self, request):
        return 'Session'
