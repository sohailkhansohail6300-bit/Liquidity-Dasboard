from django.conf import settings
from django.db import models
from django.utils import timezone


class Ticket(models.Model):
    """A support ticket (e.g. DB-1052)."""

    class Status(models.TextChoices):
        OURS = 'ours', 'Needs our reply'
        CLIENT = 'client', 'Waiting on client'
        DONE = 'done', 'Resolved'

    ref = models.CharField(max_length=16, unique=True)
    subject = models.CharField(max_length=200)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='tickets')
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name='+')
    opened_by_name = models.CharField(max_length=120)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.OURS)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    # The prototype stores display strings ("21 Oct 2026", "Yesterday", "Today, 09:42"); keep them verbatim.
    created_label = models.CharField(max_length=30)
    updated_label = models.CharField(max_length=30)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['company', 'status'], name='ticket_company_status_idx'),
        ]

    def __str__(self):
        return self.ref


class TicketMessage(models.Model):
    class Sender(models.TextChoices):
        CLIENT = 'client', 'Client'
        SUPPORT = 'support', 'Support'

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=8, choices=Sender.choices)
    author_name = models.CharField(max_length=160)
    posted_at = models.DateTimeField(default=timezone.now)
    posted_label = models.CharField(max_length=30)
    text = models.TextField()

    class Meta:
        ordering = ['posted_at', 'id']
