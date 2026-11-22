import re
from datetime import date, datetime, timedelta

from django.conf import settings
from django.utils import timezone

EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$')


def reference_date():
    """The prototype's fixed "today" (D.TODAY) used only by sample-data derivations."""
    return settings.DELTABLOCK_REFERENCE_DATE


def real_today():
    return timezone.now().date()


def fmt_date(d):
    """'04 Oct 2026' - the prototype's en-GB day/short-month/year label."""
    return d.strftime('%d %b %Y') if d else ''


def fmt_last(dt):
    """'23 Oct · 14:32 UTC'."""
    if not dt:
        return None
    dt = timezone.localtime(dt, timezone.utc) if timezone.is_aware(dt) else dt
    return '%d %s · %s UTC' % (dt.day, dt.strftime('%b'), dt.strftime('%H:%M'))


def msg_stamp(dt):
    """Ticket message time label: 'Today · 09:42' for today, otherwise '21 Oct · 10:05'."""
    dt = timezone.localtime(dt, timezone.utc)
    if dt.date() == real_today():
        return 'Today · ' + dt.strftime('%H:%M')
    return '%s · %s' % (dt.strftime('%d %b'), dt.strftime('%H:%M'))


def updated_label(dt):
    """Ticket 'Updated' column: 'Today, 09:42', 'Yesterday' or '18 Sep 2026'."""
    dt = timezone.localtime(dt, timezone.utc)
    today = real_today()
    if dt.date() == today:
        return 'Today, ' + dt.strftime('%H:%M')
    if dt.date() == today - timedelta(days=1):
        return 'Yesterday'
    return fmt_date(dt.date())


def clean_spaces(v):
    return re.sub(r'\s+', ' ', str(v if v is not None else '')).strip()


def to_float(v):
    return None if v is None else float(v)
