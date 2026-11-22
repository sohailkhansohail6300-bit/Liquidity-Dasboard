"""Deterministic sample-data calculations ported 1:1 from the prototype's JavaScript.

These functions are pure (no Django imports) so the arithmetic can be compared directly with the
original ``app.js`` / page scripts. The same inputs always give the same numbers, which is what keeps
Overview, Market activity, Trade history and Peer comparison consistent with one another.

Every operation order mirrors the JavaScript so IEEE-754 results are identical.
"""
import datetime as dt
import math

MASK = 0xFFFFFFFF


def js_round(x):
    """JavaScript Math.round: halves go towards +infinity."""
    return int(math.floor(x + 0.5))


def rng(seed):
    """Linear congruential generator from ``App.rng``."""
    state = [int(seed) & MASK]

    def nxt():
        state[0] = (state[0] * 1664525 + 1013904223) & MASK
        return state[0] / 4294967296
    return nxt


def seed_of(company_id):
    h = 7
    for ch in company_id:
        h = (h * 31 + ord(ch)) & MASK
    return h


def series(company_id, price, vol30, spread30, n, salt=0):
    """Daily price / volume / spread sample series (``App.series``)."""
    r = rng(seed_of(company_id) + (salt or 0))
    p = price * 0.93
    out = []
    for _ in range(n):
        p += (r() - 0.46) * price * 0.03
        p = max(price * 0.75, min(price * 1.18, p))
        v = vol30 / 30 * (0.35 + r() * 1.3)
        s = spread30 * (0.8 + r() * 0.45)
        out.append({'p': p, 'v': v, 's': s})
    k = price / out[n - 1]['p']
    for x in out:
        x['p'] *= k
    return out


def add_iso(day, n):
    return (day + dt.timedelta(days=n)).isoformat()


def _split(r, n, total, lo, hi, wts=None):
    """Integers that add up exactly to ``total``."""
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


N_DAYS = 364


def market_model(company, kpi, sub_start, today):
    """One consistent daily market model per company (the ``model()`` function of market.html).

    ``company``: dict with id, price, vol30, spread30. ``kpi``: {'24h','7d','30d','since'} -> dict(vol, share).
    ``sub_start``: contract start date or None. ``today``: the reference date.
    """
    n = N_DAYS
    cid = company['id']
    r = rng(seed_of(cid) + 4242)
    price = series(cid, company['price'], company['vol30'], company['spread30'], n, 5)
    tot = [0] * n
    dele = [0] * n
    days_since = round_half_up((today - sub_start).days) if sub_start else n
    s0 = max(0, n - 1 - days_since)
    k24, k7, k30, ks = kpi['24h'], kpi['7d'], kpi['30d'], kpi['since']
    d24 = js_round(k24['vol'] * k24['share'] / 100)
    d7 = js_round(k7['vol'] * k7['share'] / 100)
    d30 = js_round(k30['vol'] * k30['share'] / 100)
    dS = js_round(ks['vol'] * ks['share'] / 100)
    segs = [[n - 1, n - 1, k24['vol'], d24],
            [n - 7, n - 2, k7['vol'] - k24['vol'], d7 - d24],
            [n - 30, n - 8, k30['vol'] - k7['vol'], d30 - d7]]
    if s0 < n - 30:
        segs.append([s0, n - 31, ks['vol'] - k30['vol'], dS - d30])
    for g in segs:
        cnt = g[1] - g[0] + 1
        t = _split(r, cnt, g[2], 0.6, 1.4)
        dl = _split(r, cnt, g[3], 0.8, 1.2, t)
        for k in range(cnt):
            tot[g[0] + k] = t[k]
            dele[g[0] + k] = dl[k]
    avg = company['vol30'] / 30
    for i in range(s0 if s0 < n - 30 else n - 30):
        tot[i] = js_round(avg * (0.5 + r() * 1.0))
        dele[i] = 0
    days = []
    for i in range(n):
        days.append({'iso': add_iso(today, i - (n - 1)), 'p': price[i]['p'], 'tot': tot[i], 'del': dele[i]})
    return {'days': days, 'd24': d24, 'd30': d30, 'dS': dS}


def round_half_up(x):
    return int(math.floor(x + 0.5))


# --------------------------------------------------------------------------- trades
VENUES = {'XETRA': ['XETRA', 'Tradegate', 'XETRA'],
          'Euronext': ['Euronext Amsterdam', 'Cboe Europe', 'Euronext Amsterdam']}


def trades(company):
    """30 sample trades per company (``trades()`` of trades.html). Newest first."""
    r = rng(seed_of(company['id']) + 99)
    out = []
    day, minute, no = 23, 14 * 60 + 22, 88241
    price = company['price']
    for _ in range(30):
        side = 'Buy' if r() < 0.52 else 'Sell'
        sh = js_round((500 + r() * r() * 24000) / 100) * 100
        pr = price * (0.985 + r() * 0.03)
        venues = VENUES[company['exch']]
        iso = '2026-10-%02d' % day
        stamp_day, stamp_min = day, minute
        no -= js_round(8 + r() * 60)
        trade_id = company['code'] + '-' + str(no)
        venue = venues[int(math.floor(r() * len(venues)))]
        out.append({'iso': iso, 'day': stamp_day, 'minute': stamp_min, 'id': trade_id, 'side': side,
                    'sh': sh, 'pr': pr, 'val': sh * pr, 'venue': venue})
        minute -= js_round(60 + r() * 240)
        if minute < 9 * 60:
            minute = 17 * 60 + js_round(r() * 25)
            day -= (3 if day % 7 == 6 else 1)
            if day < 1:
                day = 1
    return out


# -------------------------------------------------------------------- peer comparison
PEER_PERIODS = {
    '3m': [0.97, 1.04, 0.99, 0.96],
    '6m': [0.93, 1.08, 0.98, 0.92],
    '1y': [0.88, 1.13, 0.97, 0.88],
}
MEASURE_KEYS = ['vol', 'spr', 'tim', 'turn']   # volume, spread (bps), time in market (%), turnover (%)


def peer_data(company_id, kpi30, lo, hi, median, period):
    """The company's value and the peer range for one period (``pdata`` of comparison.html).

    ``kpi30``: dict with vol, spr, tim, turn. ``lo`` / ``hi`` / ``median``: lists in MEASURE_KEYS order.
    """
    f = PEER_PERIODS[period]
    r = rng(seed_of(company_id) + ord(period[0]) * 7 + len(period))
    out = []
    for i, key in enumerate(MEASURE_KEYS):
        drift = 1 + (f[i] - 1) * 0.8 + (r() - 0.5) * 0.06
        v = kpi30[key] * drift
        if i == 2:
            v = min(99.9, v)
        out.append({'v': v, 'lo': lo[i] * f[i], 'hi': hi[i] * f[i], 'med': median[i] * f[i]})
    return out


def peer_position(kpi30, median):
    """Overview "How you compare": state of each 30-day figure against the peer median."""
    out = []
    for i, key in enumerate(MEASURE_KEYS):
        v = kpi30[key]
        med = median[i]
        d = (v - med) / med
        if abs(d) < 0.1:
            state = ['inf', 'Near median']
        else:
            up = d > 0
            good = (not up) if i == 1 else up
            state = ['ok' if good else 'warn', 'Above median' if up else 'Below median']
        out.append({'measure': key, 'value': v, 'median': med, 'state': state})
    return out
