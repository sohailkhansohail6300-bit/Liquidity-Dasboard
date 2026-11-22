"""Formatting helpers that reproduce what the prototype's JavaScript printed."""
import datetime as dt
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.utils import timezone

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def to_fixed(value, digits):
    """JavaScript ``Number.prototype.toFixed``: rounds half up on the exact binary value."""
    q = Decimal(1).scaleb(-digits)
    return str(Decimal(value).quantize(q, rounding=ROUND_HALF_UP))


def js_round(value):
    """JavaScript ``Math.round`` (halves round towards +infinity)."""
    import math
    return int(math.floor(value + 0.5))


def num(value):
    """``Number(n).toLocaleString('en-GB')`` for integers and plain floats."""
    if isinstance(value, float) and not float(value).is_integer():
        text = f'{value:,}'
        return text
    return f'{int(value):,}'


def fmt_date(value):
    """'23 Oct 2026' (day zero padded), the format of ``App.today()`` / ``fmtDate``."""
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        value = value.astimezone(dt.timezone.utc).date() if timezone.is_aware(value) else value.date()
    return f'{value.day:02d} {MONTHS[value.month - 1]} {value.year}'


def fmt_day_month_time(value):
    """'23 Oct · 14:32 UTC' (the "latest data" label used on company and feed rows)."""
    if value is None:
        return None
    value = value.astimezone(dt.timezone.utc)
    return f'{value.day} {MONTHS[value.month - 1]} · {value:%H:%M} UTC'


def reference_date():
    """The date the sample data is pinned to (the prototype's TODAY constant)."""
    return dt.date.fromisoformat(settings.PORTAL_REFERENCE_DATE)


def today_label():
    return fmt_date(timezone.localdate())


def stamp_label(now=None):
    """'Today · 09:42' as written on new ticket messages."""
    now = timezone.localtime(now or timezone.now())
    return f'Today · {now:%H:%M}'


def updated_label(now=None):
    """'Today, 09:42' as written in the ticket list's Updated column."""
    now = timezone.localtime(now or timezone.now())
    return f'Today, {now:%H:%M}'


def access_log_stamp(value):
    """Matches ``Intl.DateTimeFormat('en-GB', {weekday:'short', ... hour12:true}).format(d).replace(',', '')``,
    which yields e.g. 'Thu 22 Oct 2026, 08:41 am' (only the first comma is removed)."""
    value = value.astimezone(dt.timezone.utc)
    hour = value.hour % 12 or 12
    suffix = 'am' if value.hour < 12 else 'pm'
    return (f'{WEEKDAYS[value.weekday()]} {value.day:02d} {MONTHS[value.month - 1]} {value.year}, '
            f'{hour:02d}:{value:%M} {suffix}')
