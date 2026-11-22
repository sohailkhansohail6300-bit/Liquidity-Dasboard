'use client';
import Link from 'next/link';
import { useApp } from '@/components/AppProvider';
import { Badge, Spark } from '@/components/ui';
import { useLoad, useLocalPref } from '@/hooks/useLoad';
import { api } from '@/lib/api';
import { daysUntil, num } from '@/lib/format';
import { position, series } from '@/lib/derive';

const PER = { '24h': '24 hours', '7d': '7 days', '30d': '30 days' };
const PTS = { '24h': 12, '7d': 7, '30d': 30 };
function sgn(v, d) { return (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d); }

function KpiCard({ label, val, unit, d, good, note, vals, per }) {
  return (
    <div className="card kpi-card p-4">
      <div className="metric-label">{label}</div>
      <div className="metric mt-2">{val}{unit ? <>{' '}<small className="metric-unit">{unit}</small></> : null}</div>
      <div className="mt-1 min-h-[1.25rem] text-xs text-cap">{note}</div>
      <div className="mt-3 flex items-center justify-between gap-2"><span className={'bd ' + (good ? 'ok' : 'warn')}>{d} vs prior {per}</span><Spark vals={vals} /></div>
    </div>
  );
}
function Row({ h, t, l, href }) {
  return (
    <li className="border-t py-3 first:border-t-0 first:pt-0"><div className="text-xs text-cap">{h}</div><div className="mt-0.5 text-sm font-medium">{t}</div><Link className="text-sm text-mut underline" href={href}>{l}</Link></li>
  );
}

export default function Dashboard() {
  const app = useApp();
  const { co, me, meta } = app;
  const [per, setPer] = useLocalPref('period', '30d', ['24h', '7d', '30d']);
  const guest = me.role === 'guest';
  const { data } = useLoad(async () => {
    const [kp, peers, reports, tix, subs] = await Promise.all([
      api.get('/companies/' + co.id + '/kpi/'),
      api.get('/peer-groups/'),
      api.get('/reports/'),
      guest ? Promise.resolve([]) : api.get('/tickets/'),
      guest ? Promise.resolve({}) : api.get('/subscriptions/')
    ]);
    return { kp, peers, reports, tix, subs };
  }, [co.id, guest]);
  if (!data) return null;

  const K = data.kp.kpi, k = K[per], since = K.since, pl = PER[per], sr = series(co, PTS[per]);
  const feedOk = co.feed[0] === 'ok', timOk = k.tim >= co.timTarget, sprOk = k.spr <= co.sprTarget;
  const issues = [];
  if (!timOk) issues.push('Time in market is ' + k.tim.toFixed(1) + '%, below the ' + co.timTarget + '% target.');
  if (!sprOk) issues.push('Average spread is ' + k.spr.toFixed(1) + ' bps, above the ' + co.sprTarget + ' bps target.');
  if (!feedOk) issues.push('Trade data feed: ' + co.feed[1].toLowerCase() + '. Figures may be incomplete until it catches up.');
  const banner = issues.length
    ? (<div className="card mb-6 flex gap-3 border-l-4 p-4" style={{ borderLeftColor: '#F2B705' }}><span className="bd warn shrink-0 self-start">Needs a look</span><ul className="text-sm text-mut">{issues.map((i) => <li key={i}>{i}</li>)}</ul></div>)
    : (<div className="card mb-6 flex items-center gap-3 border-l-4 p-4" style={{ borderLeftColor: '#146C34' }}><span className="bd ok">On target</span><span className="text-sm text-mut">Time in market and spread are both within target for the last {pl}.</span></div>);

  const peerGroup = data.peers[0];
  const pos = position(K['30d'], peerGroup);
  const share = k.share, dash = (share / 100 * 289).toFixed(1);
  const rep = data.reports[0];
  const tix = data.tix.filter((t) => t.company === co.id && t.status !== 'done');
  const sub = data.subs[co.id];
  const days = sub ? daysUntil(sub.renewIso, meta.today) : NaN;

  return (
    <>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="page-title">Overview</h1>
          <p className="mt-2 flex flex-wrap items-center gap-2 text-sm text-mut">
            <b className="text-ink">{co.name}</b><span>{co.exch} · {co.code}</span><span className="mono text-ink">&euro;{co.price.toFixed(3)}</span><Badge kind={co.feed[0]}>{co.feed[1]}</Badge><span className="text-cap">Latest data {co.last}</span>{guest ? <span className="chip">Read-only guest access</span> : null}
          </p>
        </div>
        <div className="seg" role="group" aria-label="Period">
          {Object.keys(PER).map((p) => <button type="button" key={p} data-per={p} aria-pressed={p === per} onClick={() => setPer(p)}>{p === '24h' ? '24 hours' : p === '7d' ? '7 days' : '30 days'}</button>)}
        </div>
      </div>
      {banner}
      <div className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard per={per} label="Time in market" val={k.tim.toFixed(1) + '%'} unit="" d={sgn(k.timD, 1) + ' pp'} good={k.timD >= 0} note={<>Target {co.timTarget}% · {timOk ? 'met' : 'not met'}</>} vals={sr.map((x) => x.s * -1)} />
        <KpiCard per={per} label="Volume traded" val={num(k.vol)} unit="shares" d={sgn(k.volD, 1) + '%'} good={k.volD >= 0} note="Across all venues" vals={sr.map((x) => x.v)} />
        <KpiCard per={per} label="Average spread" val={k.spr.toFixed(1)} unit="bps" d={sgn(k.sprD, 1) + ' bps'} good={k.sprD <= 0} note={<>Target ≤ {co.sprTarget} bps · {sprOk ? 'met' : 'not met'}</>} vals={sr.map((x) => x.s)} />
        <KpiCard per={per} label="Turnover" val={k.turn.toFixed(2) + '%'} unit="" d={sgn(k.turnD, 2) + ' pp'} good={k.turnD >= 0} note="Share of free float traded" vals={sr.map((x, i) => x.v * (1 + i / 60))} />
      </div>
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <section className="card p-5">
            <div className="mb-3 flex items-start justify-between gap-3"><div><h2 className="font-semibold">How you compare</h2><p className="text-sm text-cap">Against {peerGroup.name} · anonymised · last 30 days</p></div><Link className="btn btn-s" href="/comparison">Full comparison</Link></div>
            <ul>
              {pos.map((p) => (
                <li key={p.label} className="flex items-center justify-between gap-3 border-t py-2.5 text-sm first:border-t-0"><span>{p.label}</span><span className="flex items-center gap-3"><span className="mono">{p.value}</span><Badge kind={p.state[0]}>{p.state[1]}</Badge></span></li>
              ))}
            </ul>
          </section>
          <section className="card p-5">
            <div className="mb-4 flex items-start justify-between gap-3"><div><h2 className="font-semibold">Deltablock contribution</h2><p className="text-sm text-cap">Share of all volume traded in {co.name}, last {pl}</p></div></div>
            <div className="flex flex-wrap items-center gap-6">
              <div className="relative shrink-0">
                <svg viewBox="0 0 120 120" className="h-28 w-28 -rotate-90" role="img" aria-label={'Deltablock share of volume ' + share + ' percent'}><circle cx="60" cy="60" r="46" fill="none" strokeWidth="16" className="c-grid" /><circle cx="60" cy="60" r="46" fill="none" strokeWidth="16" strokeDasharray={dash + ' 289'} strokeLinecap="round" stroke="#F2B705" /></svg>
                <div className="absolute inset-0 grid place-items-center text-lg font-semibold">{share}%</div>
              </div>
              <dl className="grid flex-1 grid-cols-2 gap-x-6 gap-y-3 text-sm"><div><dt className="text-xs text-cap">Since contract start</dt><dd className="font-semibold mono">{since.share}%</dd></div><div className="col-span-2"><Link className="text-sm font-medium underline" href="/market">See Deltablock against the whole market &rarr;</Link></div></dl>
            </div>
          </section>
        </div>
        <section className="card p-5">
          <h2 className="mb-3 font-semibold">Latest</h2>
          <ul>
            <Row h="NEWEST REPORT" t={<>{rep.title} · {rep.period}</>} l="Open reports" href="/reports" />
            {guest ? null : (
              <>
                <Row h="SUPPORT" t={tix.length ? tix.length + ' open ticket' + (tix.length > 1 ? 's' : '') : 'No open tickets'} l={tix.length ? 'View tickets' : 'Contact support'} href="/tickets" />
                <Row h="SUBSCRIPTION" t={<>{sub.plan}{days <= 60 ? ' · renews in ' + days + ' days' : ' · active'}</>} l="View subscription" href="/subscription" />
              </>
            )}
          </ul>
        </section>
      </div>
    </>
  );
}
