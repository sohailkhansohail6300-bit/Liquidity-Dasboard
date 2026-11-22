from django.db import models


class KpiSnapshot(models.Model):
    """Headline KPIs for one company and period (the prototype's ``KPI`` table).

    ``*_delta`` columns are the change versus the prior period and are empty for the
    "since contract start" row.
    """

    class Period(models.TextChoices):
        DAY = '24h', 'Last 24 hours'
        WEEK = '7d', 'Last 7 days'
        MONTH = '30d', 'Last 30 days'
        SINCE = 'since', 'Since contract start'

    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='kpis')
    period = models.CharField(max_length=8, choices=Period.choices)
    time_in_market = models.DecimalField(max_digits=5, decimal_places=1)
    time_in_market_delta = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    volume = models.BigIntegerField()
    volume_delta = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    spread = models.DecimalField(max_digits=6, decimal_places=1)
    spread_delta = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    turnover = models.DecimalField(max_digits=6, decimal_places=2)
    turnover_delta = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    deltablock_share = models.DecimalField(max_digits=5, decimal_places=1)
    active_traders = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'period'], name='uniq_kpi_company_period'),
        ]


class MarketStat(models.Model):
    """Market-wide trade count and buy/sell split that sit next to the KPIs."""
    company = models.OneToOneField('companies.Company', on_delete=models.CASCADE, related_name='market_stat')
    market_trades_30d = models.PositiveIntegerField()
    buy_pct = models.DecimalField(max_digits=4, decimal_places=1)


class PeerGroup(models.Model):
    """An anonymised peer group. Only aggregate statistics are stored, never peer identities."""
    key = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=80)
    size = models.PositiveIntegerField()
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']


class PeerMeasure(models.Model):
    """Median and range of one measure within a peer group."""

    class Measure(models.TextChoices):
        VOLUME = 'vol', 'Average daily volume'
        SPREAD = 'spr', 'Average spread'
        TIME = 'tim', 'Time at minimum spread'
        TURNOVER = 'turn', 'Market turnover'

    group = models.ForeignKey(PeerGroup, on_delete=models.CASCADE, related_name='measures')
    measure = models.CharField(max_length=8, choices=Measure.choices)
    median = models.DecimalField(max_digits=12, decimal_places=2)
    low = models.DecimalField(max_digits=12, decimal_places=2)
    high = models.DecimalField(max_digits=12, decimal_places=2)
    range_label = models.CharField(max_length=40)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['group', 'measure'], name='uniq_peer_measure_group_measure'),
        ]


class Report(models.Model):
    """A published PDF report. Shared by every company in the sample data, as in the prototype."""
    title = models.CharField(max_length=120)
    period_label = models.CharField(max_length=60)
    published_on = models.DateField()
    file = models.FileField(upload_to='reports/')
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position', '-published_on', 'id']


class Feed(models.Model):
    """Freshness of one data feed (trades or reference prices) for a company."""

    class State(models.TextChoices):
        OK = 'ok', 'Up to date'
        WARN = 'warn', 'Delayed'

    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='feeds')
    name = models.CharField(max_length=40)
    latest_at = models.DateTimeField()
    expected_interval = models.CharField(max_length=20)
    records_today = models.PositiveIntegerField(default=0)
    state = models.CharField(max_length=8, choices=State.choices, default=State.OK)
    label = models.CharField(max_length=40)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']


class Trade(models.Model):
    """An executed sample trade shown on Trade history."""

    class Side(models.TextChoices):
        BUY = 'Buy', 'Buy'
        SELL = 'Sell', 'Sell'

    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='trades')
    position = models.PositiveSmallIntegerField(help_text='Order in the list, newest first.')
    trade_ref = models.CharField(max_length=24)
    executed_at = models.DateTimeField()
    side = models.CharField(max_length=4, choices=Side.choices)
    shares = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=18, decimal_places=12)
    value = models.DecimalField(max_digits=22, decimal_places=8)
    venue = models.CharField(max_length=60)

    class Meta:
        ordering = ['company', 'position']
        constraints = [
            models.UniqueConstraint(fields=['company', 'trade_ref'], name='uniq_trade_company_ref'),
        ]
        indexes = [
            models.Index(fields=['company', 'executed_at'], name='trade_company_time_idx'),
        ]
