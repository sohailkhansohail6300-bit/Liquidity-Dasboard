from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class Company(models.Model):
    """A listed company served by Deltablock. ``id`` is a short slug (c1, c2, elite, ...)."""

    class Feed(models.TextChoices):
        NONE = 'none', 'Not connected'
        OK = 'ok', 'Up to date'
        WARN = 'warn', 'Delayed'

    id = models.CharField(primary_key=True, max_length=32)
    position = models.PositiveIntegerField(default=0, db_index=True)
    name = models.CharField(max_length=60)
    legal_name = models.CharField(max_length=90)
    exchange = models.CharField(max_length=40)
    ticker = models.CharField(max_length=10)
    is_custom = models.BooleanField(default=False, help_text='Added by an administrator after the sample data.')

    reference_price = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    volume_30d = models.BigIntegerField(null=True, blank=True)
    spread_30d = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    trades_30d = models.PositiveIntegerField(null=True, blank=True)
    trade_value_30d = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)

    feed_state = models.CharField(max_length=8, choices=Feed.choices, default=Feed.NONE)
    feed_label = models.CharField(max_length=40, default='Not connected')
    last_data_at = models.DateTimeField(null=True, blank=True)
    time_in_market_target = models.PositiveSmallIntegerField(null=True, blank=True)
    spread_target = models.PositiveSmallIntegerField(null=True, blank=True)

    # Company profile (approved values). Free text on purpose: clients type "12%" or "120,000,000".
    shares_outstanding = models.CharField(max_length=120, blank=True, default='')
    free_float = models.CharField(max_length=120, blank=True, default='')
    insiders_pct = models.CharField(max_length=120, blank=True, default='')
    institutions_pct = models.CharField(max_length=120, blank=True, default='')
    contact_email = models.CharField(max_length=254, blank=True, default='')
    contact_phone = models.CharField(max_length=120, blank=True, default='')
    address = models.CharField(max_length=200, blank=True, default='')

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name='+')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'id']
        verbose_name_plural = 'companies'
        constraints = [
            models.UniqueConstraint(Lower('exchange'), Lower('ticker'), name='uniq_company_exchange_ticker_ci'),
        ]

    def __str__(self):
        return self.name


class CompanyAccess(models.Model):
    """Who can see a company, and whether they may run its Team (``can_manage``)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_access')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='access')
    can_manage = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'company access'
        constraints = [
            models.UniqueConstraint(fields=['user', 'company'], name='uniq_company_access_user_company'),
        ]
        indexes = [
            models.Index(fields=['company', 'can_manage'], name='access_company_manage_idx'),
        ]

    def __str__(self):
        return f'{self.user_id} -> {self.company_id}'


class ProfileReview(models.Model):
    """A client's proposed change to the company profile, waiting for (or past) admin review."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    ref = models.CharField(max_length=16, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='profile_reviews')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(default=timezone.now)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name='+')
    submitted_by_name = models.CharField(max_length=120, blank=True, default='')
    submitted_by_email = models.CharField(max_length=254, blank=True, default='')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name='+')
    reviewed_by_name = models.CharField(max_length=120, blank=True, default='')
    note = models.CharField(max_length=300, blank=True, default='')

    class Meta:
        ordering = ['-submitted_at', '-id']
        indexes = [
            models.Index(fields=['company', 'status'], name='review_company_status_idx'),
        ]

    def __str__(self):
        return self.ref


class ProfileReviewChange(models.Model):
    """One changed field inside a ProfileReview."""
    review = models.ForeignKey(ProfileReview, on_delete=models.CASCADE, related_name='changes')
    field = models.CharField(max_length=20)
    old_value = models.CharField(max_length=200, blank=True, default='')
    new_value = models.CharField(max_length=200, blank=True, default='')
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']
        constraints = [
            models.UniqueConstraint(fields=['review', 'field'], name='uniq_review_change_field'),
        ]
