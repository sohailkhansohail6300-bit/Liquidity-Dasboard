"""Deterministic sample-data derivations migrated 1:1 from the original prototype (js/app.js and the inline
scripts of market.html, trades.html and comparison.html).

Every function here is pure (no Django, no database) and reproduces the original JavaScript arithmetic exactly,
including its 32-bit LCG random generator and ``Math.round`` semantics, so that the migrated application shows the
same chart series, sparklines, trade list and peer ranges as the prototype.
"""
import math
from datetime import date, timedelta

MASK32 = 0xFFFFFFFF


def js_round(x):
    """JavaScript Math.round (ties go towards +infinity)."""
    return int(math.floor(x + 0.5))


def rng(seed):
    """Linear congruential generator from js/app.js (``rng``)."""
    state = [seed & MASK32]

    def nxt():
        state[0] = (state[0] * 1664525 + 1013904223) & MASK32
        return state[0] / 4294967296

    return nxt


def seed_of(key):
    """String hash from js/app.js (``seedOf``). The original hashed UTF-16 code units; ids are ASCII."""
    h = 7
    for ch in key:
        h = (h * 31 + ord(ch)) & MASK32
    return h


def series(company_key, price, vol30, spread30, n, salt=0):
    """Deterministic price / volume / spread series (``App.series``)."""
    r = rng(seed_of(company_key) + salt)
    p = price * 0.93
    out = []
    for _ in range(n):
        p += (r() - 0.46) * price * 0.03
        p = max(price * 0.75, min(price * 1.18, p))
        out.append({'p': p, 'v': vol30 / 30 * (0.35 + r() * 1.3), 's': spread30 * (0.8 + r() * 0.45)})
    k = price / out[n - 1]['p']
    for x in out:
        x['p'] *= k
    return out


# --------------------------------------------------------------------------------------------- market.html model
MARKET_DAYS = 364


def _split(r, n, total, lo, hi, wts=None):
    """Integers that add up exactly to ``total`` (``split`` in market.html)."""
    w = []
    s = 0
    for i in range(n):
        w.append((wts[i] if wts else 1) * (lo + r() * (hi - lo)))
        s += w[i]
    out = []
    acc = 0
    for i in range(n):
        out.append(int(math.floor(total * w[i] / s)))
        acc += out[i]
    rem = total - acc
    i = 0
    while rem > 0:
        out[i % n] += 1
        rem -= 1
        i += 1
    return out


def market_model(company_key, price, vol30, spread30, kpi, subscription_start, reference_date):
    """One consistent daily model per company (``model`` in market.html).

    ``kpi`` maps '24h', '7d', '30d', 'since' to dicts with ``vol`` and ``share``.
    ``subscription_start`` is a ``date`` or None. Returns a list of daily dicts
    ``{iso, p, tot, del}`` for the last 364 days, oldest first.
    """
    N = MARKET_DAYS
    r = rng(seed_of(company_key) + 4242)
    pr = series(company_key, price, vol30, spread30, N, 5)
    tot = [0] * N
    dele = [0] * N
    days_since = (reference_date - subscription_start).days if subscription_start else N
    s0 = max(0, N - 1 - days_since)
    d24 = js_round(kpi['24h']['vol'] * kpi['24h']['share'] / 100)
    d7 = js_round(kpi['7d']['vol'] * kpi['7d']['share'] / 100)
    d30 = js_round(kpi['30d']['vol'] * kpi['30d']['share'] / 100)
    dS = js_round(kpi['since']['vol'] * kpi['since']['share'] / 100)
    segs = [
        [N - 1, N - 1, kpi['24h']['vol'], d24],
        [N - 7, N - 2, kpi['7d']['vol'] - kpi['24h']['vol'], d7 - d24],
        [N - 30, N - 8, kpi['30d']['vol'] - kpi['7d']['vol'], d30 - d7],
    ]
    if s0 < N - 30:
        segs.append([s0, N - 31, kpi['since']['vol'] - kpi['30d']['vol'], dS - d30])
    for g in segs:
        n = g[1] - g[0] + 1
        t = _split(r, n, g[2], 0.6, 1.4)
        dl = _split(r, n, g[3], 0.8, 1.2, t)
        for k in range(n):
            tot[g[0] + k] = t[k]
            dele[g[0] + k] = dl[k]
    avg = vol30 / 30
    for i in range(s0 if s0 < N - 30 else N - 30):
        tot[i] = js_round(avg * (0.5 + r() * 1.0))
        dele[i] = 0
    days = []
    for i in range(N):
        days.append({
            'iso': (reference_date + timedelta(days=i - (N - 1))).isoformat(),
            'p': pr[i]['p'], 'tot': tot[i], 'del': dele[i],
        })
    return {'days': days, 'd24': d24, 'd30': d30, 'dS': dS}


# --------------------------------------------------------------------------------------------- trades.html list
VENUES = {
    'XETRA': ['XETRA', 'Tradegate', 'XETRA'],
    'Euronext': ['Euronext Amsterdam', 'Cboe Europe', 'Euronext Amsterdam'],
}


def sample_trades(company_key, code, exchange, price):
    """The 30 sample trades of trades.html (``trades``). Returns dicts oldest-first order is NOT applied:
    the list is newest first exactly like the original."""
    r = rng(seed_of(company_key) + 99)
    out = []
    day, minute, no = 23, 14 * 60 + 22, 88241
    venues = VENUES[exchange]
    for _ in range(30):
        side = 'Buy' if r() < 0.52 else 'Sell'
        sh = js_round((500 + r() * r() * 24000) / 100) * 100
        pr = price * (0.985 + r() * 0.03)
        # the original evaluates `v[Math.floor(r()*v.length)]` after building id, which consumes one more draw
        no -= js_round(8 + r() * 60)
        venue = venues[int(math.floor(r() * len(venues)))]
        out.append({
            'day': day, 'minute': minute, 'ref': '%s-%d' % (code, no), 'side': side,
            'shares': sh, 'price': pr, 'value': sh * pr, 'venue': venue,
        })
        minute -= js_round(60 + r() * 240)
        if minute < 9 * 60:
            minute = 17 * 60 + js_round(r() * 25)
            day -= 3 if day % 7 == 6 else 1
            if day < 1:
                day = 1
    return out


# --------------------------------------------------------------------------------------------- comparison.html
PERIOD_FACTORS = {
    '3m': {'label': 'Last 3 months', 'f': [0.97, 1.04, 0.99, 0.96]},
    '6m': {'label': 'Last 6 months', 'f': [0.93, 1.08, 0.98, 0.92]},
    '1y': {'label': 'Last 1 year', 'f': [0.88, 1.13, 0.97, 0.88]},
}
KPI_KEYS = ['vol', 'spr', 'tim', 'turn']


def peer_period_data(company_key, kpi30, group, period):
    """Per-measure ``{v, lo, hi, med}`` for a company against a peer group and period (``pdata``)."""
    f = PERIOD_FACTORS[period]['f']
    r = rng(seed_of(company_key) + ord(period[0]) * 7 + len(period))
    out = []
    for i in range(4):
        drift = 1 + (f[i] - 1) * 0.8 + (r() - 0.5) * 0.06
        v = kpi30[KPI_KEYS[i]] * drift
        if i == 2:
            v = min(99.9, v)
        out.append({'v': v, 'lo': group['lo'][i] * f[i], 'hi': group['hi'][i] * f[i], 'med': group['median'][i] * f[i]})
    return out


def peer_position(kpi30, group):
    """Position of a company against a peer group (``App.position``): raw values plus the state tag."""
    labels = [('Average daily volume', 'shares'), ('Average spread', 'bps'), ('Time at minimum spread', '%'), ('Market turnover', '%')]
    out = []
    for i, (label, unit) in enumerate(labels):
        v = kpi30[KPI_KEYS[i]]
        med = group['median'][i]
        d = (v - med) / med
        if abs(d) < 0.1:
            st = ['inf', 'Near median']
        else:
            up = d > 0
            st = [('ok' if ((not up) if i == 1 else up) else 'warn'), 'Above median' if up else 'Below median']
        out.append({'label': label, 'unit': unit, 'value': v, 'median': med, 'range': group['range'][i], 'state': st})
    return out
