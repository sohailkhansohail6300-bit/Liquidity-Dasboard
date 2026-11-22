import datetime as dt

from django.conf import settings
from django.db import models
from django.utils import timezone


class SignupLink(models.Model):
    """A company-based, single-use sign-up link. It reserves no person."""

    class Status(models.TextChoices):
        UNUSED = 'unused', 'Unused'
        USED = 'used', 'Used'
        EXPIRED = 'expired', 'Expired'      # also used for revoked links

    ref = models.CharField(max_length=16, unique=True)
    token = models.CharField(max_length=96, unique=True)
    companies = models.ManyToManyField('companies.Company', related_name='signup_links')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name='+')
    created_on = models.DateField(default=timezone.localdate)
    expires_on = models.DateField()
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.UNUSED)
    revoked_on = models.DateField(null=True, blank=True)
    used_on = models.DateField(null=True, blank=True)
    used_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name='+')
    used_by_email = models.CharField(max_length=254, blank=True, default='')
    used_by_name = models.CharField(max_length=120, blank=True, default='')

    class Meta:
        ordering = ['-created_on', '-id']

    def state(self):
        """unused | used | expired, evaluated against the real clock (as the prototype did)."""
        if self.status == self.Status.USED:
            return 'used'
        if self.status == self.Status.EXPIRED:
            return 'expired'
        if self.expires_on and self.expires_on < timezone.localdate():
            return 'expired'
        return 'unused'

    def __str__(self):
        return self.ref


class AccessRequest(models.Model):
    """Someone asked for access from the login page."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    ref = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=120)
    email = models.CharField(max_length=254)
    company_text = models.CharField(max_length=160)
    message = models.TextField(blank=True, default='', max_length=1000)
    received_on = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name='+')
    reviewed_by_name = models.CharField(max_length=120, blank=True, default='')
    reviewed_on = models.DateField(null=True, blank=True)
    link = models.ForeignKey(SignupLink, null=True, blank=True, on_delete=models.SET_NULL, related_name='requests')

    class Meta:
        ordering = ['-received_on', '-id']


class AccessLogEntry(models.Model):
    """One row of the admin "Access log": who signed in, when, and which company they opened."""
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name='+')
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60, blank=True, default='')
    email = models.CharField(max_length=254)
    company_label = models.CharField(max_length=60)
    # Lower-cased "stamp | iso | first | last | full name | email | company", exactly what the
    # prototype's search matched against.
    search_text = models.TextField(editable=False)

    class Meta:
        ordering = ['-occurred_at', '-id']
        verbose_name_plural = 'access log entries'


class AuditEvent(models.Model):
    """Append-only record of sensitive admin actions and access changes (not shown in the UI)."""
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name='+')
    actor_email = models.CharField(max_length=254, blank=True, default='')
    action = models.CharField(max_length=60, db_index=True)
    target_type = models.CharField(max_length=40, blank=True, default='')
    target_id = models.CharField(max_length=64, blank=True, default='')
    detail = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-occurred_at', '-id']


def default_link_expiry(days):
    return timezone.localdate() + dt.timedelta(days=days)
