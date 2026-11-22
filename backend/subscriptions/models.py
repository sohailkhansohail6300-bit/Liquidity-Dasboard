from django.db import models


class Subscription(models.Model):
    """One contract per company. A company without a row is shown as "Not assigned"."""

    class Plan(models.TextChoices):
        ESSENTIALS = 'Liquidity Essentials', 'Liquidity Essentials'
        PLUS = 'Liquidity Plus', 'Liquidity Plus'
        IR = 'Investor Relations', 'Investor Relations'

    class Status(models.TextChoices):
        ACTIVE = 'ok', 'Active'
        RENEWS_SOON = 'warn', 'Renews soon'
        EXPIRED = 'bad', 'Expired'

    company = models.OneToOneField('companies.Company', on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=40, choices=Plan.choices)
    term = models.CharField(max_length=60)
    start_date = models.DateField()
    end_date = models.DateField()
    renewal_date = models.DateField()
    auto_renew = models.CharField(max_length=200)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.ACTIVE)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.company_id}: {self.plan}'


class SubscriptionService(models.Model):
    """A contracted service line (name and scope). Website pages are never services."""
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=120)
    scope = models.CharField(max_length=300, blank=True, default='')
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']


class Statement(models.Model):
    """An invoice or billing statement listed on the Statements page."""

    class State(models.TextChoices):
        PAID = 'ok', 'Paid'
        DUE = 'warn', 'Due'

    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='statements')
    document = models.CharField(max_length=80)
    period_label = models.CharField(max_length=60)
    issued_on = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    state = models.CharField(max_length=8, choices=State.choices, default=State.PAID)
    due_on = models.DateField(null=True, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['company', 'position', 'id']
