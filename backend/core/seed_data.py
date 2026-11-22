"""Demonstration / sample data migrated from the prototype's js/data.js.

Nothing in this module is real financial or market data. It is loaded by ``manage.py seed_demo`` for local
demonstration only. Values are copied one-to-one from the original file; derived labels (for example
"23 Oct · 14:32 UTC") are rebuilt from the typed values below.
"""
from datetime import date, datetime

REFERENCE_DATE = date(2026, 10, 23)   # D.TODAY in the prototype

COMPANIES = [
    dict(slug='c1', name='Company 1', exch='XETRA', code='C1', price='0.842', vol30=184200, spread30='14.2', trades30=1284, value30='€2.84M',
         feed=('ok', 'Up to date'), last=datetime(2026, 10, 23, 14, 32), tim_target='85', spr_target='20', fee='4800',
         legal='Company 1 AG', shares='120,000,000', float='85,000,000', insiders='12%', institutions='48%',
         email='contact@company1.example', phone='+49 69 000 1000', address='Hauptstrasse 1, 60311 Frankfurt, Germany'),
    dict(slug='c2', name='Company 2', exch='Euronext', code='C2', price='1.264', vol30=212840, spread30='17.8', trades30=1486, value30='€3.91M',
         feed=('warn', 'Delayed 2h'), last=datetime(2026, 10, 23, 12, 18), tim_target='85', spr_target='18', fee='6400',
         legal='Company 2 N.V.', shares='96,500,000', float='61,200,000', insiders='9%', institutions='55%',
         email='contact@company2.example', phone='+31 20 000 2000', address='Damrak 20, 1012 Amsterdam, Netherlands'),
    dict(slug='elite', name='elite', exch='XETRA', code='ELT', price='2.108', vol30=85560, spread30='12.6', trades30=612, value30='€1.74M',
         feed=('ok', 'Up to date'), last=datetime(2026, 10, 23, 14, 29), tim_target='85', spr_target='16', fee='5600',
         legal='elite Holding SE', shares='48,000,000', float='30,400,000', insiders='21%', institutions='40%',
         email='contact@elite.example', phone='+49 89 000 3000', address='Maximilianstrasse 8, 80539 Munich, Germany'),
]

# KPI per company and period: tim, timD, vol, volD, spr, sprD, turn, turnD, share, traders
KPI = {
    'c1': {
        '24h': dict(tim=96.0, timD=2.1, vol=11400, volD=8.4, spr=14.8, sprD=-0.2, turn=0.05, turnD=0.01, share=6.8, traders=4),
        '7d': dict(tim=95.2, timD=0.8, vol=48900, volD=3.1, spr=14.5, sprD=-0.4, turn=0.21, turnD=0.02, share=6.5, traders=5),
        '30d': dict(tim=96.0, timD=1.4, vol=184200, volD=5.2, spr=14.2, sprD=-0.6, turn=0.84, turnD=0.06, share=6.3, traders=5),
        'since': dict(tim=94.1, vol=1398000, spr=15.1, turn=6.2, share=6.1, traders=5),
    },
    'c2': {
        '24h': dict(tim=79.6, timD=-3.2, vol=14100, volD=-6.5, spr=19.4, sprD=1.1, turn=0.04, turnD=-0.01, share=9.4, traders=3),
        '7d': dict(tim=81.0, timD=-1.5, vol=60300, volD=-2.2, spr=18.6, sprD=0.5, turn=0.18, turnD=-0.02, share=9.6, traders=4),
        '30d': dict(tim=82.1, timD=0.4, vol=212840, volD=1.9, spr=17.8, sprD=-0.3, turn=0.64, turnD=0.03, share=9.1, traders=4),
        'since': dict(tim=80.7, vol=1612000, spr=18.9, turn=5.1, share=8.7, traders=4),
    },
    'elite': {
        '24h': dict(tim=98.1, timD=0.6, vol=5300, volD=12.0, spr=12.9, sprD=-0.5, turn=0.07, turnD=0.01, share=4.2, traders=2),
        '7d': dict(tim=97.6, timD=0.2, vol=21800, volD=7.4, spr=12.7, sprD=-0.3, turn=0.29, turnD=0.04, share=4.4, traders=3),
        '30d': dict(tim=97.3, timD=0.9, vol=85560, volD=9.7, spr=12.6, sprD=-0.8, turn=1.02, turnD=0.12, share=4.6, traders=3),
        'since': dict(tim=96.4, vol=612000, spr=13.4, turn=7.8, share=5.0, traders=3),
    },
}

MARKET = {'c1': (44300, '52.0'), 'c2': (52100, '48.5'), 'elite': (21400, '50.5')}   # market_trades30, buy_pct

# Order of measures: volume, spread (bps), time in market (%), turnover (%)
PEER_GROUPS = [
    dict(key='ind', name='European industrials', n=8, median=[162400, 18.6, 82.4, 0.72], range=['92k – 281k', '11.4 – 31.2', '61% – 98%', '0.31% – 1.4%'], lo=[92000, 11.4, 61, 0.31], hi=[281000, 31.2, 98, 1.4]),
    dict(key='cap', name='Companies with similar market cap', n=12, median=[148000, 16.9, 86.1, 0.66], range=['70k – 240k', '10.2 – 26.8', '66% – 99%', '0.28% – 1.2%'], lo=[70000, 10.2, 66, 0.28], hi=[240000, 26.8, 99, 1.2]),
    dict(key='all', name='All listed peers', n=46, median=[121500, 21.3, 78.9, 0.58], range=['18k – 410k', '8.9 – 44.0', '42% – 99%', '0.09% – 1.9%'], lo=[18000, 8.9, 42, 0.09], hi=[410000, 44.0, 99, 1.9]),
]

SUBSCRIPTIONS = {
    'c1': dict(plan='Liquidity Essentials', term='Annual service', start=date(2026, 3, 1), renewal=date(2027, 3, 1),
               auto_renew='Renews automatically unless cancelled 60 days before the end date',
               services=[('Liquidity provision', 'Continuous two-sided quotes in Company 1 shares on XETRA'), ('Spread and time-in-market monitoring', 'Daily coverage'), ('Liquidity reporting', 'Monthly liquidity review')]),
    'c2': dict(plan='Liquidity Plus', term='Annual service', start=date(2025, 11, 15), renewal=date(2026, 11, 15),
               auto_renew='Renews automatically unless cancelled 60 days before the end date',
               services=[('Liquidity provision', 'Continuous two-sided quotes in Company 2 shares on Euronext, intraday coverage'), ('Spread and time-in-market monitoring', 'Intraday coverage'), ('Liquidity reporting', 'Monthly review and quarterly trading summary'), ('Performance reviews', 'Quarterly review with Deltablock')]),
    'elite': dict(plan='Investor Relations', term='Annual service', start=date(2026, 7, 1), renewal=date(2027, 6, 30),
                  auto_renew='Renews automatically unless cancelled 60 days before the end date',
                  services=[('Liquidity provision', 'Continuous two-sided quotes in elite shares on XETRA'), ('Spread and time-in-market monitoring', 'Daily coverage'), ('Liquidity reporting', 'Monthly liquidity review'), ('Shareholder analysis', 'Quarterly')]),
}

REPORTS = [
    ('Monthly liquidity review', 'September 2026', date(2026, 10, 4), 'reports/monthly-liquidity-review.pdf'),
    ('Trading activity summary', 'Q3 2026', date(2026, 10, 2), 'reports/trading-activity-summary.pdf'),
    ('Annual market review', '2025', date(2026, 1, 12), 'reports/annual-market-review.pdf'),
]

# ref, token, companies, created, expires, status, used_on, used_by_email
LINKS = [
    dict(ref='L5', token='lnk-b7k2x4', companies=['c2', 'elite'], created=date(2026, 10, 20), expires=date(2026, 11, 3), status='unused'),
    dict(ref='L4', token='lnk-x91q3m', companies=['c2'], created=date(2026, 9, 28), expires=date(2026, 10, 12), status='expired'),
    dict(ref='L3', token='lnk-m4n8d2', companies=['c1', 'c2', 'elite'], created=date(2026, 9, 21), expires=date(2026, 10, 5), status='used', used_on=date(2026, 9, 22), used_by='diego@acme.co'),
    dict(ref='L2', token='lnk-77aa9k', companies=['elite'], created=date(2026, 9, 14), expires=date(2026, 9, 28), status='used', used_on=date(2026, 9, 14), used_by='omar@elite.com'),
    dict(ref='L1', token='lnk-12cc5t', companies=['c1'], created=date(2026, 9, 2), expires=date(2026, 9, 16), status='used', used_on=date(2026, 9, 3), used_by='aisha.khan@gmail.com'),
]

REQUESTS = [
    dict(ref='R4', name='Priya Nair', email='priya.nair@helios-power.example', company='Helios Power AG', message='We are listed on XETRA and would like to see liquidity reporting for our shares.', received=date(2026, 10, 21), status='pending'),
    dict(ref='R3', name='Marc Dubois', email='m.dubois@nordvik.example', company='Nordvik Industries', message='Interested in peer comparison against European industrials.', received=date(2026, 10, 20), status='pending'),
    dict(ref='R2', name='Hanna Weber', email='hanna@weber-capital.example', company='Weber Capital', message='Please share pricing for the investor relations plan.', received=date(2026, 10, 15), status='approved'),
    dict(ref='R1', name='Chris Walker', email='chris@walker-media.example', company='Walker Media', message='Looking for market data for a news article.', received=date(2026, 10, 9), status='rejected'),
]

# key, first, last, email, type, owner, companies, manages, tenant(key), status, via, invited_by(key), token
PEOPLE = [
    dict(key='p1', first='Khan', last='Abid', email='khan@gmail.com', type='admin', companies=[], manages=[], status='active'),
    dict(key='p2', first='Xavier', last='Young', email='xy@gmail.com', type='admin', companies=[], manages=[], status='active'),
    dict(key='p3', first='Aisha', last='Khan', email='aisha.khan@gmail.com', type='client', owner=True, companies=['c1'], manages=['c1'], tenant='p3', status='active', via='Sign-up link'),
    dict(key='p4', first='Mia', last='Fischer', email='mia.fischer@company1.example', type='colleague', companies=['c1'], manages=[], tenant='p3', status='active', via='Team invite', invited_by='p3'),
    dict(key='p5', first='Lena', last='Brandt', email='lena@brandt.io', type='colleague', companies=['c1'], manages=[], tenant='p3', status='pending', via='Team invite', invited_by='p3', token='colleague-lena-9x2m'),
    dict(key='p6', first='Jordan', last='Lee', email='jordan@example.com', type='guest', companies=['c1'], manages=[], tenant='p3', status='pending', via='Team invite', invited_by='p3', token='guest-jordan-7f3k'),
    dict(key='p7', first='Omar', last='Siddiqui', email='omar@elite.com', type='client', owner=True, companies=['elite'], manages=['elite'], tenant='p7', status='active', via='Sign-up link'),
    dict(key='p8', first='Diego', last='Alvarez', email='diego@acme.co', type='client', owner=True, companies=['c1', 'c2', 'elite'], manages=['c1', 'c2', 'elite'], tenant='p8', status='active', via='Sign-up link'),
    dict(key='p9', first='Priya', last='Shah', email='priya.shah@acme.co', type='colleague', companies=['c2', 'elite'], manages=['c2'], tenant='p8', status='active', via='Team invite', invited_by='p8'),
    dict(key='p10', first='Marco', last='Rossi', email='marco@rossi-advisory.example', type='guest', companies=['c2'], manages=[], tenant='p8', status='active', via='Team invite', invited_by='p8'),
    dict(key='p11', first='Sara', last='Malik', email='sara.m@gmail.com', type='client', owner=True, companies=['c2'], manages=['c2'], tenant='p11', status='pending', via='Sign-up link (expired)'),
]

# Tickets: ref, subject, company, opened_by(key), status, created, updated (see seed command for relative labels), messages
# message tuple: (sender, author_key|None, author_name, when, text) with when = (days_ago_from_today|None, date|None, 'HH:MM')
TICKETS = [
    dict(ref='DB-1052', subject='Add a custom peer group', company='c1', by='p3', status='client', created=date(2026, 10, 21), updated=('rel', 1, '15:40'), messages=[
        ('client', 'p3', 'Aisha Khan', ('abs', date(2026, 10, 21), '10:05'), 'Could we compare Company 1 against three named competitors instead of the standard industrials group?'),
        ('support', None, 'Mara · Deltablock support', ('abs', date(2026, 10, 21), '15:40'), 'Named peers are not possible because peer data is anonymised, but we can build a custom group by sector and market cap. Which size range would you like?')]),
    dict(ref='DB-1048', subject='September report clarification', company='c1', by='p3', status='ours', created=date(2026, 10, 19), updated=('rel', 0, '09:42'), messages=[
        ('client', 'p3', 'Aisha Khan', ('abs', date(2026, 10, 19), '16:12'), 'The September report shows turnover of 0.84%, but the overview shows 0.05% for the last 24 hours. Which period does the report use?'),
        ('support', None, 'Mara · Deltablock support', ('abs', date(2026, 10, 20), '09:30'), 'The report uses the full calendar month, the overview uses the last 24 hours. We are adding the period to the report footer.'),
        ('client', 'p3', 'Aisha Khan', ('abs', date(2026, 10, 20), '11:02'), 'Thanks. Can you also confirm that time in market uses the same calendar month?'),
        ('support', None, 'Mara · Deltablock support', ('rel', 0, '09:42'), 'Confirmed, both use the calendar month. I will send the updated PDF shortly.')]),
    dict(ref='DB-1039', subject='Exchange data delay', company='c2', by='p8', status='client', created=date(2026, 10, 17), updated=('rel', 1, '14:10'), messages=[
        ('client', 'p8', 'Diego Alvarez', ('abs', date(2026, 10, 17), '08:50'), 'The Company 2 trade feed looks about two hours behind. Is this on your side or the exchange?'),
        ('support', None, 'Mara · Deltablock support', ('abs', date(2026, 10, 21), '14:10'), 'The delay comes from the Euronext delivery. It is catching up. Could you tell us if you still see gaps after 18:00 UTC?')]),
    dict(ref='DB-0982', subject='Invoice DB-2026-007', company='c1', by='p3', status='done', created=date(2026, 9, 15), updated=('abs', date(2026, 9, 18), '10:20'), messages=[
        ('client', 'p3', 'Aisha Khan', ('abs', date(2026, 9, 15), '09:15'), 'Please resend invoice DB-2026-007, it did not reach our accounting inbox.'),
        ('support', None, 'Mara · Deltablock support', ('abs', date(2026, 9, 18), '10:20'), 'Resent to accounting@company1.example. You can also download it under Statements.')]),
]

ACCESS_LOG = [
    ('Khan', 'Abid', 'khan@gmail.com', 'Admin'), ('Aisha', 'Khan', 'aisha.khan@gmail.com', 'Company 1'), ('Omar', 'Siddiqui', 'omar@elite.com', 'elite'),
    ('Diego', 'Alvarez', 'diego@acme.co', 'Company 2'), ('Mia', 'Fischer', 'mia.fischer@company1.example', 'Company 1'), ('Priya', 'Shah', 'priya.shah@acme.co', 'Company 2'),
    ('Xavier', 'Young', 'xy@gmail.com', 'Admin'), ('Marco', 'Rossi', 'marco@rossi-advisory.example', 'Company 2'), ('Diego', 'Alvarez', 'diego@acme.co', 'elite'), ('Aisha', 'Khan', 'aisha.khan@gmail.com', 'Company 1'),
]
ACCESS_LOG_TOTAL = 1096

# company, feed, latest, expected, records, status
FEEDS = [
    ('c1', 'Trades', datetime(2026, 10, 23, 14, 32), '15 min', 1284, ('ok', 'Up to date')),
    ('c1', 'Reference prices', datetime(2026, 10, 23, 14, 30), '15 min', 412, ('ok', 'Up to date')),
    ('c2', 'Trades', datetime(2026, 10, 23, 12, 18), '15 min', 986, ('warn', 'Delayed')),
    ('c2', 'Reference prices', datetime(2026, 10, 23, 14, 28), '15 min', 398, ('ok', 'Up to date')),
    ('elite', 'Trades', datetime(2026, 10, 23, 14, 29), '15 min', 756, ('ok', 'Up to date')),
    ('elite', 'Reference prices', datetime(2026, 10, 23, 14, 31), '15 min', 240, ('ok', 'Up to date')),
]

# Statements (accounting.html derives these from BASE invoice numbers and the company fee)
INVOICE_BASE = {'c1': 9, 'c2': 19, 'elite': 29}
