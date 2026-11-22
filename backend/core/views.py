import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.access import get_access
from accounts.models import User
from administration.models import AccessLogEntry, AccessRequest, SignupLink
from companies.models import Company, CompanyAccess, ProfileReview, ProfileReviewChange
from market.models import KpiSnapshot, MarketStat, PeerGroup, Report, Trade
from subscriptions.models import Statement, Subscription, SubscriptionService
from support.models import Ticket, TicketMessage
from core.exceptions import ApiError


def fail(message, status=400, code=None, errors=None, field=None):
    return ApiError(message, status, errors, code, field)


def me_payload(user):
    if not user or not user.is_authenticated:
        return None
    access = get_access(type('Request', (), {'user': user})())
    return {
        'id': user.pk,
        'name': user.name,
        'first': user.first_name,
        'last': user.last_name,
        'email': user.email,
        'kind': user.kind,
        'role': access.role,
        'isOwner': user.is_owner,
        'companies': [c.id for c in Company.objects.filter(access__user=user).distinct()] if user.kind != 'admin' else [],
        'manages': access.manages,
        'allowed': access.allowed,
        'tenantEmail': user.tenant_owner.email if user.tenant_owner else (user.email if user.is_owner else None),
        'status': user.status,
    }


def access_company(request, company_id):
    access = get_access(request)
    if not access.can_view(company_id):
        raise fail('You do not have access to that company.', 403, 'forbidden')
    company = Company.objects.filter(pk=company_id).first()
    if not company:
        raise fail('You do not have access to that company.', 403, 'forbidden')
    return company


def company_payload(company):
    c = company
    feed = c.feed_state
    feed_label = c.feed_label
    return {
        'id': c.id,
        'name': c.name,
        'legal': c.legal_name,
        'exch': c.exchange,
        'code': c.ticker,
        'price': float(c.reference_price) if c.reference_price is not None else None,
        'vol30': c.volume_30d,
        'spread30': float(c.spread_30d) if c.spread_30d is not None else None,
        'trades30': c.trades_30d,
        'value30': None,
        'feed': [feed, feed_label],
        'last': None,
        'timTarget': c.time_in_market_target,
        'sprTarget': c.spread_target,
        'fee': None,
        'shares': c.shares_outstanding,
        'float': c.free_float,
        'insiders': c.insiders_pct,
        'institutions': c.institutions_pct,
        'email': c.contact_email,
        'phone': c.contact_phone,
        'address': c.address,
        'custom': c.is_custom,
        'hasData': c.kpis.exists(),
    }


class MetaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'today': settings.DELTABLOCK_REFERENCE_DATE.isoformat(),
            'demoMode': settings.DELTABLOCK_DEMO_MODE,
        })


class DemoSamplesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not settings.DELTABLOCK_DEMO_MODE:
            raise fail('Not found.', 404, 'not_found')
        signup = SignupLink.objects.filter(status='unused').first()
        invitation = User.objects.filter(status='pending', setup_token__isnull=False).first()
        return Response({
            'signupToken': signup.token if signup else None,
            'guestToken': invitation.setup_token if invitation else None,
        })


class CsrfView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'csrfToken': get_token(request)})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = str(request.data.get('email') or '').strip()
        password = str(request.data.get('password') or '')
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise fail('No account uses that email address. Ask your administrator, or request access.', 400, 'login_failed')
        if user.status != User.Status.ACTIVE:
            raise fail('That account has not been set up yet. Open the invitation link you were given.', 400, 'login_failed')
        authenticated = authenticate(request, username=user.email, password=password)
        if not authenticated:
            raise fail('The email or password is incorrect.', 400, 'login_failed')
        login(request, authenticated)
        request.session.set_expiry(settings.REMEMBER_ME_AGE if request.data.get('remember') else 0)
        return Response({'user': me_payload(authenticated)})


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response(status=204)


class MeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'user': me_payload(request.user)})


class AccountView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        first = str(request.data.get('first') or '').strip()
        last = str(request.data.get('last') or '').strip()
        email = str(request.data.get('email') or '').strip()
        errors = {}
        if not first:
            errors['first'] = 'Enter your first name.'
        elif len(first) > 60:
            errors['first'] = 'Use at most 60 characters.'
        if not last:
            errors['last'] = 'Enter your last name.'
        elif len(last) > 60:
            errors['last'] = 'Use at most 60 characters.'
        if not email or '@' not in email:
            errors['email'] = 'Enter a valid email address.'
        elif User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            errors['email'] = 'Another account already uses this email address.'
        if errors:
            raise fail('Please fix the highlighted fields.', 400, 'validation_error', errors)
        user.first_name, user.last_name, user.email = first, last, email.lower()
        user.save(update_fields=['first_name', 'last_name', 'email', 'updated_at'])
        return Response({'user': me_payload(user)})


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current = str(request.data.get('current') or '')
        new = str(request.data.get('next') or '')
        confirm = str(request.data.get('confirm') or '')
        errors = {}
        if not current:
            errors['current'] = 'Enter your current password.'
        elif not request.user.check_password(current):
            errors['current'] = 'The current password is not correct.'
        if len(new) < 12:
            errors['next'] = 'Use at least 12 characters for the password.'
        elif new != confirm:
            errors['confirm'] = 'The two passwords do not match.'
        elif current and new == current:
            errors['next'] = 'Choose a password that is different from the current one.'
        if errors:
            raise fail('Your password was not changed. Please check the highlighted fields.', 400, 'validation_error', errors)
        request.user.set_password(new)
        request.user.save(update_fields=['password', 'updated_at'])
        update_session_auth_hash(request, request.user)
        return Response(status=204)


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = str(request.data.get('email') or '').strip()
        user = User.objects.filter(email__iexact=email, status='active').first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_mail('Deltablock password reset', f'uid={uid}\ntoken={token}', settings.DEFAULT_FROM_EMAIL, [user.email])
        return Response({})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            uid = force_str(urlsafe_base64_decode(request.data.get('uid') or ''))
            user = User.objects.filter(pk=uid).first()
        except (TypeError, ValueError, OverflowError):
            user = None
        password = str(request.data.get('password') or '')
        confirm = str(request.data.get('confirm') or '')
        errors = {}
        if not user or not default_token_generator.check_token(user, str(request.data.get('token') or '')):
            raise fail('This password reset link is not valid or has expired.', 400, 'invalid')
        if len(password) < 12:
            errors['password'] = 'Use at least 12 characters for the password.'
        elif password != confirm:
            errors['confirm'] = 'The two passwords do not match.'
        if errors:
            raise fail('Please fix the highlighted fields.', 400, 'validation_error', errors)
        user.set_password(password)
        user.save(update_fields=['password', 'updated_at'])
        return Response(status=204)


class SignupLinkView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        invitation = User.objects.filter(setup_token=token, status='pending').first()
        if invitation:
            if invitation.status != 'pending':
                return Response({'state': 'invite_used'})
            companies = Company.objects.filter(access__user=invitation).distinct()
            return Response({
                'state': 'open',
                'kind': 'invite',
                'inviteType': invitation.kind,
                'name': invitation.name,
                'email': invitation.email,
                'invitedBy': invitation.invited_by.name if invitation.invited_by else invitation.invited_by_name,
                'companies': [{'id': c.id, 'name': c.name, 'exch': c.exchange} for c in companies],
            })
        link = SignupLink.objects.filter(token=token).first()
        if not link:
            return Response({'state': 'invalid'})
        state = link.state()
        if state == 'used':
            return Response({'state': 'used', 'usedOnIso': link.used_on.isoformat() if link.used_on else None})
        if state == 'expired':
            return Response({'state': 'expired'})
        companies = list(link.companies.all())
        if not companies:
            return Response({'state': 'no_companies'})
        return Response({
            'state': 'open',
            'kind': 'link',
            'companies': [{'id': c.id, 'name': c.name, 'exch': c.exchange} for c in companies],
        })

    @transaction.atomic
    def post(self, request, token):
        invitation = User.objects.select_for_update().filter(setup_token=token, status='pending').first()
        if invitation:
            name = str(request.data.get('name') or '').strip()
            password = str(request.data.get('password') or '')
            confirm = str(request.data.get('confirm') or '')
            if len(name) < 2:
                raise fail('Enter your name.', 400, 'field', {'name': 'Enter your name.'}, 'name')
            if len(password) < 12:
                raise fail('Use at least 12 characters for the password.', 400, 'field', {'password': 'Use at least 12 characters for the password.'}, 'password')
            if password != confirm:
                raise fail('The two passwords do not match.', 400, 'field', {'confirm': 'The two passwords do not match.'}, 'confirm')
            invitation.first_name = name
            invitation.last_name = ''
            invitation.status = 'active'
            invitation.setup_token = None
            invitation.set_password(password)
            invitation.save()
            login(request, invitation)
            return Response({'user': me_payload(invitation)}, status=201)

        link = SignupLink.objects.select_for_update().filter(token=token).first()
        if not link:
            raise fail('This sign-up link is not valid.', 400, 'invalid')
        state = link.state()
        if state == 'used':
            raise fail('This link was already used.', 400, 'used')
        if state == 'expired':
            raise fail('This link has expired.', 400, 'expired')
        name = str(request.data.get('name') or '').strip()
        email = str(request.data.get('email') or '').strip()
        password = str(request.data.get('password') or '')
        confirm = str(request.data.get('confirm') or '')
        if len(name) < 2:
            raise fail('Enter your name.', 400, 'field', {'name': 'Enter your name.'}, 'name')
        if '@' not in email:
            raise fail('Enter a valid email address.', 400, 'field', {'email': 'Enter a valid email address.'}, 'email')
        if len(password) < 12:
            raise fail('Use at least 12 characters for the password.', 400, 'field', {'password': 'Use at least 12 characters for the password.'}, 'password')
        if password != confirm:
            raise fail('The two passwords do not match.', 400, 'field', {'confirm': 'The two passwords do not match.'}, 'confirm')
        if User.objects.filter(email__iexact=email).exists():
            raise fail('An account with this email address already exists. Please log in to continue. If you need access to another company, contact your administrator.', 400, 'duplicate')
        companies = list(link.companies.all())
        if not companies:
            raise fail('The companies for this link no longer exist. Ask your administrator for a new link.', 400, 'invalid')
        user = User.objects.create(
            email=email.lower(), first_name=name, last_name='', kind='client',
            is_owner=True, status='active', via='Sign-up link', tenant_owner=None,
        )
        user.set_password(password)
        user.tenant_owner = user
        user.save()
        CompanyAccess.objects.bulk_create([
            CompanyAccess(user=user, company=c, can_manage=True) for c in companies
        ])
        link.status = 'used'
        link.used_on = timezone.localdate()
        link.used_by = user
        link.used_by_email = user.email
        link.used_by_name = user.name
        link.save()
        login(request, user)
        return Response({'user': me_payload(user)}, status=201)


class AccessRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        name = str(request.data.get('name') or '').strip()
        email = str(request.data.get('email') or '').strip()
        company = str(request.data.get('company') or '').strip()
        message = str(request.data.get('message') or '').strip()
        if not name:
            raise fail('Enter your name.', 400, 'field', {'name': 'Enter your name.'})
        if '@' not in email:
            raise fail('Enter a valid email address.', 400, 'field', {'email': 'Enter a valid email address.'})
        ref = f"R{AccessRequest.objects.count() + 1}"
        AccessRequest.objects.create(ref=ref, name=name, email=email, company_text=company, message=message)
        return Response({}, status=201)


class CompanyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access = get_access(request)
        companies = Company.objects.filter(pk__in=access.allowed) if not access.is_admin else Company.objects.all()
        return Response([company_payload(c) for c in companies])

    def post(self, request):
        access = get_access(request)
        if not access.is_admin:
            raise fail('Only administrators can add companies.', 403, 'forbidden')
        name = str(request.data.get('name') or '').strip()
        legal = str(request.data.get('legal') or '').strip()
        exchange = str(request.data.get('exch') or '').strip()
        ticker = str(request.data.get('code') or '').strip().upper()
        errors = {}
        if not name:
            errors['name'] = 'Enter a company name.'
        if not exchange:
            errors['exch'] = 'Enter an exchange.'
        if not ticker:
            errors['code'] = 'Enter a ticker.'
        if errors:
            raise fail('Please fix the highlighted fields.', 400, 'validation_error', errors)
        company_id = f"c{Company.objects.count() + 1}"
        company = Company.objects.create(
            id=company_id, position=Company.objects.count(), name=name, legal_name=legal,
            exchange=exchange, ticker=ticker, is_custom=True,
            reference_price=request.data.get('price') or None,
            volume_30d=request.data.get('vol30') or None,
            spread_30d=request.data.get('spread30') or None,
            trades_30d=request.data.get('trades30') or None,
            shares_outstanding=str(request.data.get('shares') or ''),
            free_float=str(request.data.get('float') or ''),
            insiders_pct=str(request.data.get('insiders') or ''),
            institutions_pct=str(request.data.get('institutions') or ''),
            contact_email=str(request.data.get('email') or ''),
            contact_phone=str(request.data.get('phone') or ''),
            address=str(request.data.get('address') or ''),
            feed_state=request.data.get('feed') if request.data.get('feed') in ('ok', 'warn') else 'none',
            feed_label='Up to date' if request.data.get('feed') == 'ok' else ('Delayed' if request.data.get('feed') == 'warn' else 'Not connected'),
            created_by=request.user,
        )
        return Response(company_payload(company), status=201)


class KpiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        company = access_company(request, company_id)
        rows = {r.period: r for r in company.kpis.all()}
        if not rows:
            raise fail('Not found.', 404, 'no_data')
        def period_payload(period):
            r = rows[period]
            data = {
                'tim': float(r.time_in_market),
                'vol': r.volume,
                'spr': float(r.spread),
                'turn': float(r.turnover),
                'share': float(r.deltablock_share),
                'traders': r.active_traders,
            }
            if period != 'since':
                data.update({
                    'timD': float(r.time_in_market_delta) if r.time_in_market_delta is not None else None,
                    'volD': float(r.volume_delta) if r.volume_delta is not None else None,
                    'sprD': float(r.spread_delta) if r.spread_delta is not None else None,
                    'turnD': float(r.turnover_delta) if r.turnover_delta is not None else None,
                })
            return data
        market = getattr(company, 'market_stat', None)
        subscription = getattr(company, 'subscription', None)
        return Response({
            'kpi': {p: period_payload(p) for p in ('24h', '7d', '30d', 'since') if p in rows},
            'market': {'marketTrades30': market.market_trades_30d, 'buyPct': float(market.buy_pct)} if market else None,
            'contractStartIso': subscription.start_date.isoformat() if subscription else None,
        })


class PeerGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = []
        for group in PeerGroup.objects.all().prefetch_related('measures'):
            measures = {m.measure: m for m in group.measures.all()}
            result.append({
                'id': group.key,
                'name': group.name,
                'n': group.size,
                'median': [float(measures[k].median) for k in ('vol', 'spr', 'tim', 'turn')],
                'range': [measures[k].range_label for k in ('vol', 'spr', 'tim', 'turn')],
                'lo': [float(measures[k].low) for k in ('vol', 'spr', 'tim', 'turn')],
                'hi': [float(measures[k].high) for k in ('vol', 'spr', 'tim', 'turn')],
            })
        return Response(result)


class ReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response([
            {
                'title': r.title,
                'period': r.period_label,
                'publishedIso': r.published_on.isoformat(),
                'href': '/' + str(r.file).replace('\\', '/'),
            }
            for r in Report.objects.all()
        ])


class TradeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        company = access_company(request, company_id)
        qs = company.trades.all()
        total = qs.count()
        from_iso = request.query_params.get('from')
        to_iso = request.query_params.get('to')
        side = request.query_params.get('side', 'All trades')
        query = str(request.query_params.get('q') or '').strip().lower()
        if from_iso:
            qs = qs.filter(executed_at__date__gte=from_iso)
        if to_iso:
            qs = qs.filter(executed_at__date__lte=to_iso)
        if side and side != 'All trades':
            qs = qs.filter(side=side)
        if query:
            qs = [t for t in qs if query in f"{t.trade_ref} {t.venue}".lower()]
        return Response({
            'total': total,
            'results': [{
                'id': t.trade_ref,
                'executedAt': timezone.localtime(t.executed_at).strftime('%Y-%m-%dT%H:%M:%S'),
                'side': t.side,
                'shares': t.shares,
                'price': float(t.price),
                'value': float(t.value),
                'venue': t.venue,
            } for t in qs],
        })


class StatementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        access = get_access(request)
        if access.role == 'guest':
            raise fail('Guests have read-only access to this area.', 403, 'forbidden')
        company = access_company(request, company_id)
        return Response([
            {
                'document': s.document,
                'period': s.period_label,
                'issuedIso': s.issued_on.isoformat(),
                'amount': float(s.amount),
                'statusKind': s.state,
                'statusLabel': 'Paid' if s.state == 'ok' else 'Due',
            } for s in company.statements.all()
        ])


class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access = get_access(request)
        if access.role == 'guest':
            raise fail('Guests cannot view subscriptions.', 403, 'forbidden')
        company_ids = access.allowed
        companies = Company.objects.filter(pk__in=company_ids) if not access.is_admin else Company.objects.all()
        result = {}
        today = timezone.localdate()
        for company in companies:
            sub = getattr(company, 'subscription', None)
            if not sub:
                result[company.id] = {
                    'none': True, 'plan': 'Not assigned', 'term': '\u2014',
                    'startIso': None, 'endIso': None, 'renewIso': None,
                    'status': ['dr', 'Not assigned'], 'autoRenew': '', 'services': [],
                }
            else:
                if sub.renewal_date < today:
                    status = ['bad', 'Expired']
                elif (sub.renewal_date - today).days <= 60:
                    status = ['warn', 'Renews soon']
                else:
                    status = ['ok', 'Active']
                result[company.id] = {
                    'none': False,
                    'plan': sub.plan,
                    'term': sub.term,
                    'startIso': sub.start_date.isoformat(),
                    'endIso': sub.end_date.isoformat(),
                    'renewIso': sub.renewal_date.isoformat(),
                    'status': status,
                    'autoRenew': sub.auto_renew,
                    'services': [[s.name, s.scope] for s in sub.services.all()],
                }
        return Response(result)


def profile_review_payload(review):
    changes = {c.field: {'from': c.old_value, 'to': c.new_value} for c in review.changes.all()}
    return {
        'id': review.ref,
        'company': review.company_id,
        'status': review.status,
        'submittedOnIso': review.submitted_at.date().isoformat(),
        'by': {'name': review.submitted_by_name or (review.submitted_by.name if review.submitted_by else ''),
               'email': review.submitted_by_email or (review.submitted_by.email if review.submitted_by else '')},
        'changes': changes,
        'reviewedOnIso': review.reviewed_at.date().isoformat() if review.reviewed_at else None,
        'reviewedBy': ({'name': review.reviewed_by_name, 'email': review.reviewed_by.email} if review.reviewed_by else None),
        'note': review.note,
    }


class ProfileReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        access = get_access(request)
        company = access_company(request, company_id)
        if access.role == 'guest':
            return Response({'pending': None, 'lastDecision': None})
        pending = company.profile_reviews.filter(status='pending').first()
        decision = company.profile_reviews.filter(status__in=('approved', 'rejected')).first()
        return Response({
            'pending': profile_review_payload(pending) if pending else None,
            'lastDecision': profile_review_payload(decision) if decision else None,
        })

    def post(self, request, company_id):
        access = get_access(request)
        company = access_company(request, company_id)
        if not access.can_edit_profile(company_id):
            raise fail('Only managers can submit profile changes.', 403, 'forbidden')
        values = request.data.get('values') or {}
        field_map = {
            'legal': ('legal_name', 'legal'), 'exch': ('exchange', 'exch'),
            'shares': ('shares_outstanding', 'shares'), 'float': ('free_float', 'float'),
            'insiders': ('insiders_pct', 'insiders'), 'institutions': ('institutions_pct', 'institutions'),
            'email': ('contact_email', 'email'), 'phone': ('contact_phone', 'phone'),
            'address': ('address', 'address'),
        }
        changes = []
        for public_name, (field_name, _key) in field_map.items():
            if public_name not in values:
                continue
            old = str(getattr(company, field_name) or '')
            new = str(values[public_name] or '')
            if old != new:
                changes.append((public_name, old, new))
        if not changes:
            raise fail('Nothing has changed compared with the approved profile.', 400, 'no_changes')
        company.profile_reviews.filter(status='pending').update(status='withdrawn')
        review = ProfileReview.objects.create(
            ref=f"PR{ProfileReview.objects.count() + 101}",
            company=company, submitted_by=request.user,
            submitted_by_name=request.user.name, submitted_by_email=request.user.email,
        )
        ProfileReviewChange.objects.bulk_create([
            ProfileReviewChange(review=review, field=field, old_value=old, new_value=new, position=i)
            for i, (field, old, new) in enumerate(changes)
        ])
        return Response(profile_review_payload(review), status=201)


class PendingProfileReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, company_id):
        access = get_access(request)
        company = access_company(request, company_id)
        if not access.can_edit_profile(company_id):
            raise fail('Only managers can withdraw profile changes.', 403, 'forbidden')
        pending = company.profile_reviews.filter(status='pending').first()
        if not pending:
            raise fail('There is nothing pending.', 400, 'no_pending')
        pending.status = 'withdrawn'
        pending.save(update_fields=['status'])
        return Response(status=204)


def team_member_payload(person, caller):
    access = get_access(type('Request', (), {'user': caller})())
    p_access = CompanyAccess.objects.filter(user=person).select_related('company')
    visible = set(access.allowed)
    companies = [r.company_id for r in p_access if r.company_id in visible] if not access.is_admin else [r.company_id for r in p_access]
    manages = [r.company_id for r in p_access if r.can_manage and r.company_id in visible] if not access.is_admin else [r.company_id for r in p_access if r.can_manage]
    managers = CompanyAccess.objects.filter(user=person, can_manage=True).exists()
    return {
        'id': person.pk,
        'name': person.name,
        'email': person.email,
        'kind': person.kind,
        'isOwner': person.is_owner,
        'companies': companies,
        'companyCount': len(companies),
        'manages': manages,
        'status': person.status,
        'via': person.via,
        'token': person.setup_token if person.status == 'pending' else None,
    }


class TeamView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        company = access_company(request, company_id)
        access = get_access(request)
        if access.role == 'guest':
            raise fail('Guests cannot view team management.', 403, 'forbidden')
        people = User.objects.filter(company_access__company=company).filter(
            Q(status='active') | Q(status='pending', via='Team invite')
        ).exclude(kind='admin').distinct()
        manager_ids = set(CompanyAccess.objects.filter(company=company, can_manage=True).values_list('user_id', flat=True))
        people = sorted(people, key=lambda p: (0 if p.pk in manager_ids else 1, p.name.lower()))
        manager_names = [p.name for p in people if p.pk in manager_ids and p.status == 'active']
        return Response({
            'members': [team_member_payload(p, request.user) for p in people],
            'managers': manager_names,
        })


class TeamInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        access = get_access(request)
        if access.role == 'guest':
            raise fail('Guests have read-only access.', 403, 'forbidden')
        name = str(request.data.get('name') or '').strip()
        email = str(request.data.get('email') or '').strip()
        kind = 'guest' if request.data.get('type') == 'guest' else 'colleague'
        companies = list(dict.fromkeys(request.data.get('companies') or []))
        if '@' not in email:
            raise fail('Enter a valid email address.', 400, 'field', {'email': 'Enter a valid email address.'})
        if not companies:
            raise fail('Choose at least one company.', 400, 'field', {'companies': 'Choose at least one company.'})
        if not access.is_admin:
            for company_id in companies:
                if not access.can_manage(company_id):
                    raise fail('You can only invite people to companies whose Team you manage.', 403, 'forbidden')
        if User.objects.filter(email__iexact=email).exists():
            raise fail('That email already has an account or an invitation. An administrator can add company access from Users \u2192 Edit access.', 400, 'duplicate')
        token = f"{kind}-{secrets.token_urlsafe(12)}"
        person = User.objects.create(
            email=email.lower(), first_name=name or email.split('@')[0], last_name='',
            kind=kind, status='pending', via='Team invite', invited_by=request.user,
            tenant_owner=request.user.tenant_owner or (request.user if request.user.is_owner else None),
            setup_token=token,
        )
        person.set_unusable_password()
        person.save(update_fields=['password'])
        CompanyAccess.objects.bulk_create([
            CompanyAccess(user=person, company=Company.objects.get(pk=company_id), can_manage=False)
            for company_id in companies if Company.objects.filter(pk=company_id).exists()
        ])
        return Response(team_member_payload(person, request.user), status=201)


class TeamMemberAccessView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def put(self, request, person_id):
        access = get_access(request)
        person = User.objects.filter(pk=person_id).first()
        if not person or person.kind == 'admin':
            raise fail('That person cannot be changed here.', 404, 'not_found')
        if person.pk == request.user.pk:
            raise fail('You cannot change your own access.', 403, 'forbidden')
        selected = list(dict.fromkeys(request.data.get('companies') or []))
        if not selected:
            raise fail('Keep at least one company, or use Remove to take away all access.', 400, 'validation_error')
        for company_id in selected:
            if not access.is_admin and not access.can_manage(company_id):
                raise fail('You can only change access for companies you manage.', 403, 'forbidden')
        if not access.is_admin:
            keep = CompanyAccess.objects.filter(user=person).exclude(company_id__in=access.allowed).values_list('company_id', flat=True)
            selected = list(set(list(keep) + selected))
        CompanyAccess.objects.filter(user=person).exclude(company_id__in=selected).delete()
        for company_id in selected:
            company = Company.objects.filter(pk=company_id).first()
            if company:
                CompanyAccess.objects.get_or_create(user=person, company=company, defaults={'can_manage': False})
        return Response({})

    @transaction.atomic
    def delete(self, request, person_id):
        access = get_access(request)
        person = User.objects.filter(pk=person_id).first()
        if not person or person.kind == 'admin':
            raise fail('That person cannot be changed here.', 404, 'not_found')
        company_id = request.query_params.get('company')
        if company_id and not access.is_admin and not access.can_manage(company_id):
            raise fail('You can only remove people from companies you manage.', 403, 'forbidden')
        if company_id:
            CompanyAccess.objects.filter(user=person, company_id=company_id).delete()
        else:
            scope = access.allowed if access.is_admin else access.manages
            CompanyAccess.objects.filter(user=person, company_id__in=scope).delete()
        deleted = not CompanyAccess.objects.filter(user=person).exists()
        if deleted:
            person.delete()
        return Response({'deleted': deleted})


def ticket_payload(ticket):
    return {
        'id': ticket.ref,
        'subject': ticket.subject,
        'company': ticket.company_id,
        'by': ticket.opened_by_name,
        'status': ticket.status,
        'createdIso': ticket.created_at.date().isoformat(),
        'created': ticket.created_label,
        'updatedLabel': ticket.updated_label,
        'messages': [{
            'from': m.sender,
            'name': m.author_name,
            'at': m.posted_label,
            'atLabel': m.posted_label,
            'text': m.text,
        } for m in ticket.messages.all()],
    }


class TicketListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access = get_access(request)
        if access.role == 'guest':
            raise fail('Guests cannot view tickets.', 403, 'forbidden')
        tickets = Ticket.objects.all() if access.is_admin else Ticket.objects.filter(company_id__in=access.allowed)
        return Response([ticket_payload(t) for t in tickets.order_by('-created_at')])

    @transaction.atomic
    def post(self, request):
        access = get_access(request)
        if access.role not in ('client', 'multi'):
            raise fail('This account cannot create support tickets.', 403, 'forbidden')
        subject = str(request.data.get('subject') or '').strip()
        company_id = str(request.data.get('company') or '')
        message = str(request.data.get('message') or '').strip()
        if not subject or not access.can_view(company_id):
            raise fail('Choose a valid subject and company.', 400, 'validation_error')
        max_ref = 1051
        for ref in Ticket.objects.values_list('ref', flat=True):
            if ref.startswith('DB-'):
                try:
                    max_ref = max(max_ref, int(ref[3:]))
                except ValueError:
                    pass
        ticket = Ticket.objects.create(
            ref=f"DB-{max_ref + 1}", subject=subject,
            company=Company.objects.get(pk=company_id), opened_by=request.user,
            opened_by_name=request.user.name, status='ours',
            created_label=timezone.localdate().strftime('%d %b %Y'),
            updated_label=f"Today, {timezone.localtime().strftime('%H:%M')}",
        )
        TicketMessage.objects.create(
            ticket=ticket, sender='client', author_name=request.user.name,
            posted_label=f"Today \u00b7 {timezone.localtime().strftime('%H:%M')}", text=message,
        )
        return Response(ticket_payload(ticket), status=201)


class TicketDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ticket_id):
        access = get_access(request)
        ticket = Ticket.objects.filter(ref=ticket_id).first()
        if not ticket or not (access.is_admin or ticket.company_id in access.allowed):
            raise fail('Not found.', 404, 'not_found')
        return Response(ticket_payload(ticket))


class TicketMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ticket_id):
        access = get_access(request)
        ticket = Ticket.objects.filter(ref=ticket_id).first()
        if not ticket or not (access.is_admin or ticket.company_id in access.allowed):
            raise fail('Not found.', 404, 'not_found')
        text = str(request.data.get('text') or '').strip()
        if not text:
            raise fail('Enter a message.', 400, 'validation_error', {'text': 'Enter a message.'})
        if access.is_admin:
            sender = 'support'
            name = f"{request.user.name} \u00b7 Deltablock support"
            ticket.status = 'client'
        else:
            if access.role == 'guest':
                raise fail('Guests cannot send tickets.', 403, 'forbidden')
            sender = 'client'
            name = request.user.name
            ticket.status = 'ours'
        now = timezone.localtime()
        label = f"Today \u00b7 {now.strftime('%H:%M')}"
        TicketMessage.objects.create(ticket=ticket, sender=sender, author_name=name, posted_label=label, text=text)
        ticket.updated_label = f"Today, {now.strftime('%H:%M')}"
        ticket.updated_at = timezone.now()
        ticket.save(update_fields=['status', 'updated_label', 'updated_at'])
        return Response(ticket_payload(ticket), status=201)


class TicketStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ticket_id):
        access = get_access(request)
        ticket = Ticket.objects.filter(ref=ticket_id).first()
        if not ticket or not (access.is_admin or ticket.company_id in access.allowed):
            raise fail('Not found.', 404, 'not_found')
        status = request.data.get('status')
        if status not in ('done', 'ours'):
            raise fail('Choose a valid status.', 400, 'validation_error')
        ticket.status = status
        ticket.updated_label = f"Today, {timezone.localtime().strftime('%H:%M')}"
        ticket.updated_at = timezone.now()
        ticket.save(update_fields=['status', 'updated_label', 'updated_at'])
        return Response(ticket_payload(ticket))


def admin_user_payload(person):
    access = get_access(type('Request', (), {'user': person})())
    companies = list(CompanyAccess.objects.filter(user=person).values_list('company_id', flat=True))
    manages = list(CompanyAccess.objects.filter(user=person, can_manage=True).values_list('company_id', flat=True))
    invited_by = person.invited_by
    owner_name = ''
    if invited_by and invited_by.pk != person.pk:
        owner = person.tenant_owner or invited_by
        owner_name = owner.name if owner else ''
    return {
        'id': person.pk,
        'name': person.name,
        'first': person.first_name,
        'last': person.last_name,
        'email': person.email,
        'kind': person.kind,
        'isOwner': person.is_owner,
        'companies': companies,
        'manages': manages,
        'status': person.status,
        'via': person.via,
        'invitedBy': invited_by.name if invited_by else '',
        'ownerName': owner_name,
        'token': person.setup_token if person.status == 'pending' else None,
    }


class AdminCountsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        return Response({
            'accessRequestsPending': AccessRequest.objects.filter(status='pending').count(),
            'profileReviewsPending': ProfileReview.objects.filter(status='pending').count(),
        })


class AdminUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        return Response([admin_user_payload(u) for u in User.objects.all()])


class AdminUserAccessView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def put(self, request, person_id):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        person = User.objects.filter(pk=person_id).first()
        if not person or person.kind == 'admin':
            raise fail('That person cannot be changed here.', 404, 'not_found')
        company_ids = list(dict.fromkeys(request.data.get('companies') or []))
        manages = set(request.data.get('manages') or [])
        if not company_ids:
            raise fail('Choose at least one company.', 400, 'validation_error')
        CompanyAccess.objects.filter(user=person).delete()
        for company_id in company_ids:
            company = Company.objects.filter(pk=company_id).first()
            if company:
                CompanyAccess.objects.create(
                    user=person, company=company,
                    can_manage=person.kind != 'guest' and company_id in manages,
                )
        return Response({})

    def delete(self, request, person_id):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        person = User.objects.filter(pk=person_id).first()
        if not person:
            raise fail('User not found.', 404, 'not_found')
        if person.pk == request.user.pk:
            raise fail('You cannot remove your own account.', 400, 'invalid')
        if person.kind == 'admin' and person.status != 'pending':
            raise fail('Active administrators cannot be removed here.', 400, 'invalid')
        person.delete()
        return Response(status=204)


class AdminAddAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        first = str(request.data.get('first') or '').strip()
        last = str(request.data.get('last') or '').strip()
        email = str(request.data.get('email') or '').strip()
        if not first:
            raise fail('Enter a first name.', 400, 'field', {'first': 'Enter a first name.'}, 'first')
        if not last:
            raise fail('Enter a last name.', 400, 'field', {'last': 'Enter a last name.'}, 'last')
        if '@' not in email:
            raise fail('Enter a valid email address.', 400, 'field', {'email': 'Enter a valid email address.'}, 'email')
        if User.objects.filter(email__iexact=email).exists():
            raise fail('A user with this email address already exists. Existing clients are not converted to administrators.', 400, 'duplicate', {'email': 'A user with this email address already exists. Existing clients are not converted to administrators.'}, 'email')
        person = User.objects.create(
            email=email.lower(), first_name=first, last_name=last,
            kind='admin', status='pending', via='Added by ' + request.user.name,
            invited_by=request.user, setup_token=f"admin-{secrets.token_urlsafe(12)}",
        )
        person.set_unusable_password()
        person.save(update_fields=['password'])
        return Response(admin_user_payload(person), status=201)


def signup_link_payload(link):
    used = link.state()
    return {
        'id': link.ref,
        'token': link.token,
        'companies': list(link.companies.values_list('id', flat=True)),
        'createdIso': link.created_on.isoformat(),
        'expiresIso': link.expires_on.isoformat(),
        'status': used,
        'state': used,
        'usedOnIso': link.used_on.isoformat() if link.used_on else None,
        'usedBy': link.used_by_email,
        'usedByName': link.used_by_name,
        'createdBy': link.created_by.email if link.created_by else '',
    }


class AdminSignupLinksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        return Response([signup_link_payload(l) for l in SignupLink.objects.all()])

    def post(self, request):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        company_ids = list(dict.fromkeys(request.data.get('companies') or []))
        days = int(request.data.get('days') or 0)
        if not company_ids:
            raise fail('Choose at least one company.', 400, 'validation_error')
        if days < 1 or days > 90:
            raise fail('Choose how long the link stays valid.', 400, 'validation_error')
        ref_num = SignupLink.objects.count() + 1
        link = SignupLink.objects.create(
            ref=f"L{ref_num}", token=f"lnk-{secrets.token_urlsafe(10)}",
            created_by=request.user, expires_on=timezone.localdate() + timedelta(days=days),
        )
        link.companies.set(Company.objects.filter(pk__in=company_ids))
        request_id = request.data.get('requestId')
        if request_id:
            access_request = AccessRequest.objects.filter(ref=request_id, status='approved').first()
            if access_request:
                access_request.link = link
                access_request.save(update_fields=['link'])
        return Response(signup_link_payload(link), status=201)


class AdminSignupLinkRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, link_id):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        link = SignupLink.objects.filter(ref=link_id).first()
        if not link or link.status != 'unused':
            raise fail('Only unused links can be revoked.', 400, 'invalid')
        link.status = 'expired'
        link.revoked_on = timezone.localdate()
        link.save(update_fields=['status', 'revoked_on'])
        return Response(signup_link_payload(link))


def access_request_payload(item):
    matched = None
    if item.company_text:
        target = ''.join(ch for ch in item.company_text.lower() if ch.isalnum())
        for company in Company.objects.all():
            for name in (company.name, company.legal_name, company.ticker):
                candidate = ''.join(ch for ch in str(name).lower() if ch.isalnum())
                if target and candidate == target:
                    matched = company.id
                    break
            if matched:
                break
    return {
        'id': item.ref,
        'name': item.name,
        'email': item.email,
        'company': item.company_text,
        'message': item.message,
        'dateIso': item.received_on.isoformat(),
        'status': item.status,
        'linkId': item.link.ref if item.link else None,
        'matchedCompanyId': matched,
    }


class AdminAccessRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        return Response([access_request_payload(r) for r in AccessRequest.objects.all()])


class AdminAccessRequestDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        item = AccessRequest.objects.filter(ref=request_id).first()
        if not item:
            raise fail('Not found.', 404, 'not_found')
        if item.status != 'pending':
            raise fail('This request has already been decided.', 400, 'invalid')
        decision = request.data.get('decision')
        if decision not in ('approve', 'reject'):
            raise fail('Choose a valid decision.', 400, 'validation_error')
        item.status = 'approved' if decision == 'approve' else 'rejected'
        item.reviewed_by = request.user
        item.reviewed_by_name = request.user.name
        item.reviewed_on = timezone.localdate()
        item.save()
        return Response(access_request_payload(item))


class AdminProfileReviewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        return Response([profile_review_payload(r) for r in ProfileReview.objects.all()])


class AdminProfileReviewDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, review_id):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        review = ProfileReview.objects.select_for_update().filter(ref=review_id).first()
        if not review:
            raise fail('Not found.', 404, 'not_found')
        if review.status != 'pending':
            raise fail(f"This request has already been {review.status}.", 400, 'invalid')
        if review.submitted_by_id == request.user.pk:
            raise fail('You cannot review your own request.', 400, 'invalid')
        decision = request.data.get('decision')
        if decision not in ('approve', 'reject'):
            raise fail('Choose a valid decision.', 400, 'validation_error')
        review.status = 'approved' if decision == 'approve' else 'rejected'
        review.reviewed_at = timezone.now()
        review.reviewed_by = request.user
        review.reviewed_by_name = request.user.name
        review.note = str(request.data.get('note') or '')
        review.save()
        if decision == 'approve':
            field_map = {
                'legal': 'legal_name', 'exch': 'exchange', 'shares': 'shares_outstanding',
                'float': 'free_float', 'insiders': 'insiders_pct', 'institutions': 'institutions_pct',
                'email': 'contact_email', 'phone': 'contact_phone', 'address': 'address',
            }
            for change in review.changes.all():
                if change.field in field_map:
                    setattr(review.company, field_map[change.field], change.new_value)
            review.company.save()
        return Response(profile_review_payload(review))


class AdminSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def put(self, request, company_id):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        company = Company.objects.filter(pk=company_id).first()
        if not company:
            raise fail('Not found.', 404, 'not_found')
        plan = str(request.data.get('plan') or '')
        term = str(request.data.get('term') or '').strip()
        start_iso = str(request.data.get('startIso') or '')
        renew_iso = str(request.data.get('renewIso') or '')
        if not term:
            raise fail('Enter the service term.', 400, 'validation_error')
        try:
            start = timezone.datetime.fromisoformat(start_iso).date()
            renew = timezone.datetime.fromisoformat(renew_iso).date()
        except ValueError:
            raise fail('Enter valid dates.', 400, 'validation_error')
        if renew <= start:
            raise fail('Renewal date must be after the start date.', 400, 'validation_error')
        services = request.data.get('services') or []
        forbidden_pages = {'dashboard', 'overview', 'market', 'trades', 'comparison', 'reports', 'accounting', 'subscription', 'company', 'team', 'tickets'}
        for service in services:
            name = str(service[0] if isinstance(service, (list, tuple)) else '').strip()
            if name.lower() in forbidden_pages:
                raise fail(f'\u201c{name}\u201d is a website page, not a contracted service. Remove it from the list.', 400, 'validation_error')
        sub = getattr(company, 'subscription', None)
        if not sub:
            sub = Subscription.objects.create(
                company=company, plan=plan, term=term, start_date=start,
                end_date=renew - timedelta(days=1), renewal_date=renew,
                auto_renew=str(request.data.get('autoRenew') or ''),
            )
        else:
            sub.plan = plan
            sub.term = term
            sub.start_date = start
            sub.end_date = renew - timedelta(days=1)
            sub.renewal_date = renew
            sub.auto_renew = str(request.data.get('autoRenew') or '')
            sub.save()
        sub.services.all().delete()
        SubscriptionService.objects.bulk_create([
            SubscriptionService(subscription=sub, name=str(s[0]), scope=str(s[1]) if len(s) > 1 else '', position=i)
            for i, s in enumerate(services)
        ])
        today = timezone.localdate()
        if renew < today:
            sub.status = 'bad'
        elif (renew - today).days <= 60:
            sub.status = 'warn'
        else:
            sub.status = 'ok'
        sub.save(update_fields=['status'])
        return Response({
            'none': False,
            'plan': sub.plan,
            'term': sub.term,
            'startIso': sub.start_date.isoformat(),
            'endIso': sub.end_date.isoformat(),
            'renewIso': sub.renewal_date.isoformat(),
            'status': [sub.status, {'ok': 'Active', 'warn': 'Renews soon', 'bad': 'Expired'}[sub.status]],
            'autoRenew': sub.auto_renew,
            'services': [[s.name, s.scope] for s in sub.services.all()],
        })


class AdminFeedsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        from market.models import Feed
        return Response([
            {
                'company': f.company_id,
                'name': f.name,
                'latest': timezone.localtime(f.latest_at).strftime('%d %b · %H:%M UTC'),
                'expected': f.expected_interval,
                'records': f.records_today,
                'status': [f.state, f.label],
            } for f in Feed.objects.all()
        ])


class AdminAccessLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if get_access(request).role != 'admin':
            raise fail('Only administrators can do this.', 403, 'forbidden')
        query = str(request.query_params.get('q') or '').strip().lower()
        page = max(int(request.query_params.get('page') or 1), 1)
        size = max(int(request.query_params.get('size') or 10), 1)
        qs = AccessLogEntry.objects.all()
        if query:
            words = query.split()
            qs = [row for row in qs if all(word in row.search_text.lower() for word in words)]
        total = AccessLogEntry.objects.count()
        filtered_total = len(qs)
        start = (page - 1) * size
        rows = qs[start:start + size] if isinstance(qs, list) else qs[start:start + size]
        return Response({
            'total': total,
            'filteredTotal': filtered_total,
            'page': page,
            'pages': max((filtered_total + size - 1) // size, 1),
            'results': [{
                'stamp': row.occurred_at.strftime('%a %d %b %Y %I:%M %p').replace(' AM', ' am').replace(' PM', ' pm'),
                'first': row.first_name,
                'last': row.last_name,
                'email': row.email,
                'company': row.company_label,
            } for row in rows],
        })
