"""Compare backend/market/sim.py with the ORIGINAL JavaScript (reference numbers from ref.js)."""
import datetime as dt, json, sys
sys.path.insert(0, '/home/claude/deltablock/backend')
from common import seed_data as S
from market import sim
ref = json.load(open('/home/claude/deltablock/tools/parity/ref.json'))
today = dt.date.fromisoformat(S.TODAY)
bad = 0
def cmp(name, a, b):
    global bad
    if a != b:
        bad += 1; print('MISMATCH', name, a, b)
for cid in S.ORDER:
    c = S.COMPANIES[cid]
    co = {'id': cid, 'price': c['price'], 'vol30': c['vol30'], 'spread30': c['spread30'], 'exch': c['exch'], 'code': c['code']}
    for n, key in ((30, 'series30'), (12, 'series12'), (7, 'series7')):
        got = sim.series(cid, co['price'], co['vol30'], co['spread30'], n)
        for i, (g, r) in enumerate(zip(got, ref[cid][key])):
            for f in 'pvs': cmp(f'{cid} {key}[{i}].{f}', g[f], r[f])
    kpi = {p: {'vol': S.KPI[cid][p]['vol'], 'share': S.KPI[cid][p]['share']} for p in ('24h', '7d', '30d', 'since')}
    start = dt.date.fromisoformat(S.SUB[cid]['startIso'])
    m = sim.market_model(co, kpi, start, today)
    rm = ref[cid]['model']
    for k in ('d24', 'd30', 'dS'): cmp(f'{cid} model.{k}', m[k], rm[k])
    cmp(f'{cid} model.len', len(m['days']), len(rm['days']))
    for i, (g, r) in enumerate(zip(m['days'], rm['days'])):
        for f in ('iso', 'p', 'tot', 'del'): cmp(f'{cid} model.days[{i}].{f}', g[f], r[f])
    # also with no subscription (daysSince = N)
    tr = sim.trades(co)
    for i, (g, r) in enumerate(zip(tr, ref[cid]['trades'])):
        cmp(f'{cid} trade[{i}].iso', g['iso'], r['iso'])
        label = f"{g['day']} Oct 2026 · {g['minute']//60:02d}:{g['minute']%60:02d}"
        cmp(f'{cid} trade[{i}].dt', label, r['dt'])
        for f, rf in (('id', 'id'), ('side', 'side'), ('sh', 'sh'), ('pr', 'pr'), ('val', 'val'), ('venue', 'venue')):
            cmp(f'{cid} trade[{i}].{f}', g[f], r[rf])
    k30 = {k: S.KPI[cid]['30d'][k] for k in ('vol', 'spr', 'tim', 'turn')}
    for gi, grp in enumerate(S.PEER_GROUPS):
        rp = ref[cid]['peers'][gi]
        for per in ('3m', '6m', '1y'):
            got = sim.peer_data(cid, k30, grp['lo'], grp['hi'], grp['median'], per)
            for i, (g, r) in enumerate(zip(got, rp[per])):
                for f in ('v', 'lo', 'hi', 'med'): cmp(f'{cid} peer {grp["id"]} {per}[{i}].{f}', g[f], r[f])
        pos = sim.peer_position(k30, grp['median'])
        for i, (g, r) in enumerate(zip(pos, rp['position'])):
            cmp(f'{cid} position {grp["id"]}[{i}].state', g['state'], r['state'])
print('mismatches:', bad)
sys.exit(1 if bad else 0)
