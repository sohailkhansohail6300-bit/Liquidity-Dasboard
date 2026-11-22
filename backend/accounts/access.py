"""Who can see and manage which company. The single source of truth for authorisation.

The prototype resolved this in the browser (``App.resolve`` / ``App.can``). Here it is resolved on the
server for every request, and the browser never supplies role, company or ownership information.
"""
from companies.models import Company, CompanyAccess

ROLE_INFO = {
    'client': {'label': 'Client', 'home': '/dashboard', 'home_name': 'Overview', 'area': 'Client workspace'},
    'multi': {'label': 'Multi-company client', 'home': '/companies', 'home_name': 'Companies',
              'area': 'Client workspace'},
    'guest': {'label': 'Guest', 'home': '/dashboard', 'home_name': 'Overview', 'area': 'Guest access'},
    'admin': {'label': 'Admin', 'home': '/admin', 'home_name': 'Admin overview', 'area': 'Admin'},
}

CLIENT_NAV = [
    ('/dashboard', 'Overview'), ('/market', 'Market activity'), ('/trades', 'Trade history'),
    ('/comparison', 'Peer comparison'), ('/reports', 'Reports'), ('/accounting', 'Statements'),
    ('/subscription', 'Subscription'), ('/company', 'Company profile'), ('/team', 'Team'),
    ('/tickets', 'Support'),
]
NAV = {
    'client': CLIENT_NAV,
    'multi': [('/companies', 'Companies')] + CLIENT_NAV,
    'guest': [('/dashboard', 'Overview'), ('/market', 'Market activity'), ('/trades', 'Trade history'),
              ('/comparison', 'Peer comparison'), ('/reports', 'Reports'), ('/company', 'Company profile')],
    'admin': [('/admin', 'Admin overview'), ('/companies', 'Companies'), ('/signup-links', 'Client sign-up links'),
              ('/access-requests', 'Access requests'), ('/profile-reviews', 'Profile reviews'),
              ('/users', 'Users'), ('/admin-subscriptions', 'Subscriptions'), ('/data-health', 'Data health'),
              ('/access-log', 'Access log'), ('/tickets', 'Support tickets'), ('/wireframes', 'Screen map')],
}

CLIENT_ROLES = ('client', 'multi')
WORKSPACE_ROLES = ('client', 'multi', 'guest', 'admin')   # pages every signed-in person can open
STAFF_OR_CLIENT = ('client', 'multi', 'admin')             # Statements, Subscription, Team, Support
ADMIN_ONLY = ('admin',)


class Access:
    """Resolved access for one signed-in user."""

    def __init__(self, user):
        self.user = user
        if user.kind == 'admin':
            self.role = 'admin'
            self.allowed = list(Company.objects.values_list('id', flat=True))
            self.manages = list(self.allowed)
        else:
            rows = list(CompanyAccess.objects.filter(user=user)
                        .order_by('company__position', 'company_id')
                        .values_list('company_id', 'can_manage'))
            self.allowed = [r[0] for r in rows]
            if user.kind == 'guest':
                self.role = 'guest'
                self.manages = []
            else:
                self.role = 'multi' if len(self.allowed) > 1 else 'client'
                self.manages = [c for c, can in rows if can]

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_guest(self):
        return self.role == 'guest'

    def can_view(self, company_id):
        return company_id in self.allowed

    def can_manage(self, company_id):
        """Run a company's Team (invite, edit access, remove)."""
        return self.role != 'guest' and company_id in self.manages

    def can_edit_profile(self, company_id):
        """Submit profile changes: managers only. Admins review changes, they do not submit them."""
        return self.role not in ('admin', 'guest') and company_id in self.manages

    @property
    def scope(self):
        """Companies whose members this user may change."""
        return list(self.allowed) if self.is_admin else list(self.manages)


def get_access(request):
    """Resolve once per request."""
    cached = getattr(request, '_portal_access', None)
    if cached is None or cached.user.pk != request.user.pk:
        cached = Access(request.user)
        request._portal_access = cached
    return cached
