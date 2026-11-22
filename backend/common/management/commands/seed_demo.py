from datetime import datetime, time
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from administration.models import AccessLogEntry, AccessRequest, SignupLink
from companies.models import Company, CompanyAccess
from core import seed_data
from market.models import (
    Feed, KpiSnapshot, MarketStat, PeerGroup, PeerMeasure, Report, Trade,
)
from subscriptions.models import Statement, Subscription, SubscriptionService
from support.models import Ticket, TicketMessage


class Command(BaseCommand):
    help = 'Seed the Deltablock demonstration database'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Clear demo records before seeding')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['flush']:
            for model in (Ticket, Statement, Subscription, Report, Trade, MarketStat,
                          KpiSnapshot, PeerMeasure, PeerGroup, Feed, CompanyAccess,
                          SignupLink, AccessRequest, AccessLogEntry, Company, User):
                model.objects.all().delete()

        companies = {}
        for index, data in enumerate(seed_data.COMPANIES):
            company, _ = Company.objects.update_or_create(
                id=data['slug'],
                defaults={
                    'position': index,
                    'name': data['name'],
                    'legal_name': data['legal'],
                    'exchange': data['exch'],
                    'ticker': data['code'],
                    'reference_price': data['price'],
                    'volume_30d': data['vol30'],
                    'spread_30d': data['spread30'],
                    'trades_30d': data['trades30'],
                    'feed_state': data['feed'][0],
                    'feed_label': data['feed'][1],
                    'time_in_market_target': data['tim_target'],
                    'spread_target': data['spr_target'],
                    'shares_outstanding': data['shares'],
                    'free_float': data['float'],
                    'insiders_pct': data['insiders'],
                    'institutions_pct': data['institutions'],
                    'contact_email': data['email'],
                    'contact_phone': data['phone'],
                    'address': data['address'],
                },
            )
            companies[company.id] = company

            for period, values in seed_data.KPI[company.id].items():
                KpiSnapshot.objects.update_or_create(
                    company=company, period=period,
                    defaults={
                        'time_in_market': values['tim'],
                        'time_in_market_delta': values.get('timD'),
                        'volume': values['vol'],
                        'volume_delta': values.get('volD'),
                        'spread': values['spr'],
                        'spread_delta': values.get('sprD'),
                        'turnover': values['turn'],
                        'turnover_delta': values.get('turnD'),
                        'deltablock_share': values['share'],
                        'active_traders': values['traders'],
                    },
                )
            market_trades, buy_pct = seed_data.MARKET[company.id]
            MarketStat.objects.update_or_create(
                company=company,
                defaults={'market_trades_30d': market_trades, 'buy_pct': buy_pct},
            )
            for trade_index in range(5):
                trade_ref = f"{company.id.upper()}-{1001 + trade_index}"
                price = Decimal(str(company.reference_price or '1'))
                shares = 1000 * (trade_index + 1)
                Trade.objects.update_or_create(
                    company=company, trade_ref=trade_ref,
                    defaults={
                        'position': trade_index,
                        'executed_at': timezone.make_aware(datetime.combine(
                            seed_data.REFERENCE_DATE,
                            time(hour=14 - trade_index, minute=20),
                        )),
                        'side': 'Buy' if trade_index % 2 == 0 else 'Sell',
                        'shares': shares,
                        'price': price,
                        'value': price * shares,
                        'venue': company.exchange,
                    },
                )

        for data in seed_data.PEER_GROUPS:
            group, _ = PeerGroup.objects.update_or_create(
                key=data['key'], defaults={'name': data['name'], 'size': data['n']},
            )
            for position, measure in enumerate(('vol', 'spr', 'tim', 'turn')):
                PeerMeasure.objects.update_or_create(
                    group=group, measure=measure,
                    defaults={
                        'median': data['median'][position],
                        'low': data['lo'][position],
                        'high': data['hi'][position],
                        'range_label': data['range'][position],
                    },
                )

        for position, report in enumerate(seed_data.REPORTS):
            title, period, published, file_name = report
            Report.objects.update_or_create(
                title=title, published_on=published,
                defaults={'period_label': period, 'file': file_name, 'position': position},
            )

        for company_id, data in seed_data.SUBSCRIPTIONS.items():
            company = companies[company_id]
            sub, _ = Subscription.objects.update_or_create(
                company=company,
                defaults={
                    'plan': data['plan'],
                    'term': data['term'],
                    'start_date': data['start'],
                    'renewal_date': data['renewal'],
                    'end_date': data['renewal'].replace(year=data['renewal'].year) - __import__('datetime').timedelta(days=1),
                    'auto_renew': data['auto_renew'],
                },
            )
            sub.services.all().delete()
            SubscriptionService.objects.bulk_create([
                SubscriptionService(subscription=sub, name=name, scope=scope, position=i)
                for i, (name, scope) in enumerate(data['services'])
            ])

        people = {}
        for data in seed_data.PEOPLE:
            person, created = User.objects.update_or_create(
                email=data['email'].lower(),
                defaults={
                    'first_name': data['first'],
                    'last_name': data['last'],
                    'kind': data['type'],
                    'is_owner': data.get('owner', False),
                    'status': data['status'],
                    'via': data['via'] if 'via' in data else '',
                    'setup_token': data.get('token'),
                },
            )
            if created or not person.password:
                person.set_password(settings.DEMO_PASSWORD)
                person.save(update_fields=['password'])
            people[data['key']] = person

        for key, person in people.items():
            person_data = next(d for d in seed_data.PEOPLE if d['key'] == key)
            tenant_key = person_data.get('tenant')
            if tenant_key:
                person.tenant_owner = people[tenant_key]
            invited_key = person_data.get('invited_by')
            if invited_key:
                person.invited_by = people[invited_key]
            person.save(update_fields=['tenant_owner', 'invited_by'])
            CompanyAccess.objects.filter(user=person).delete()
            CompanyAccess.objects.bulk_create([
                CompanyAccess(user=person, company=companies[cid],
                              can_manage=cid in person_data.get('manages', []))
                for cid in person_data['companies']
            ])

        for data in seed_data.LINKS:
            link, _ = SignupLink.objects.update_or_create(
                ref=data['ref'],
                defaults={
                    'token': data['token'],
                    'created_on': data['created'],
                    'expires_on': data['expires'],
                    'status': data['status'],
                    'used_on': data.get('used_on'),
                    'used_by_email': data.get('used_by') or '',
                },
            )
            link.companies.set([companies[cid] for cid in data['companies']])

        for data in seed_data.REQUESTS:
            AccessRequest.objects.update_or_create(
                ref=data['ref'],
                defaults={
                    'name': data['name'], 'email': data['email'],
                    'company_text': data['company'], 'message': data['message'],
                    'received_on': data['received'], 'status': data['status'],
                },
            )

        for company_id, base in seed_data.INVOICE_BASE.items():
            company = companies[company_id]
            for index in range(3):
                month = 10 - index
                issued = seed_data.REFERENCE_DATE.replace(month=month)
                Statement.objects.update_or_create(
                    company=company,
                    document=f"DB-2026-{base + index:03d}",
                    defaults={
                        'period_label': issued.strftime('%B %Y'),
                        'issued_on': issued,
                        'amount': Decimal(str(company.reference_price or '1')) * (base + index),
                        'state': 'ok' if index else 'warn',
                        'position': index,
                    },
                )

        for data in seed_data.FEEDS:
            company_id, name, latest, expected, records, status = data
            aware_latest = timezone.make_aware(datetime.combine(latest.date(), latest.time()))
            Feed.objects.update_or_create(
                company=companies[company_id], name=name,
                defaults={
                    'latest_at': aware_latest, 'expected_interval': expected,
                    'records_today': records, 'state': status[0], 'label': status[1],
                },
            )

        for data in seed_data.TICKETS:
            opened_by = people[data['by']]
            created_at = timezone.make_aware(datetime.combine(data['created'], time.min))
            ticket, _ = Ticket.objects.update_or_create(
                ref=data['ref'],
                defaults={
                    'subject': data['subject'], 'company': companies[data['company']],
                    'opened_by': opened_by, 'opened_by_name': opened_by.name,
                    'status': data['status'], 'created_label': data['created'].strftime('%d %b %Y'),
                    'updated_label': 'Yesterday', 'created_at': created_at,
                    'updated_at': created_at,
                },
            )
            ticket.messages.all().delete()
            for sender, author_key, author_name, when, text in data['messages']:
                if when[0] == 'abs':
                    posted = timezone.make_aware(datetime.combine(when[1], time.fromisoformat(when[2])))
                    label = f"{posted.strftime('%d %b')} \u00b7 {posted.strftime('%H:%M')}"
                else:
                    posted = timezone.now()
                    label = f"Today \u00b7 {when[2]}"
                TicketMessage.objects.create(
                    ticket=ticket, sender=sender, author_name=author_name,
                    posted_at=posted, posted_label=label, text=text,
                )

        now = timezone.now()
        for index, data in enumerate(seed_data.ACCESS_LOG):
            first, last, email, company_label = data
            stamp = now - timezone.timedelta(days=index)
            search = f"{first.lower()} {last.lower()} {email.lower()} {company_label.lower()}"
            AccessLogEntry.objects.update_or_create(
                occurred_at=stamp, email=email,
                defaults={
                    'first_name': first, 'last_name': last,
                    'company_label': company_label, 'search_text': search,
                },
            )

        self.stdout.write(self.style.SUCCESS('Deltablock demo data seeded.'))
