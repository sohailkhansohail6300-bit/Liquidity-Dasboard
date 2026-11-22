from django.contrib import admin

from administration.models import AccessLogEntry, AccessRequest, AuditEvent, SignupLink
from companies.models import Company, CompanyAccess, ProfileReview, ProfileReviewChange
from market.models import Feed, KpiSnapshot, MarketStat, PeerGroup, PeerMeasure, Report, Trade
from subscriptions.models import Statement, Subscription, SubscriptionService
from support.models import Ticket, TicketMessage


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


for model in (
    AccessRequest, SignupLink, Company, CompanyAccess, ProfileReview,
    ProfileReviewChange, Feed, KpiSnapshot, MarketStat, PeerGroup,
    PeerMeasure, Report, Trade, Statement, Subscription, SubscriptionService,
    Ticket, TicketMessage,
):
    admin.site.register(model)

admin.site.register(AccessLogEntry, ReadOnlyAdmin)
admin.site.register(AuditEvent, ReadOnlyAdmin)
