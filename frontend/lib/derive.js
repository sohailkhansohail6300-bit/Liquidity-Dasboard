/* Deterministic sample calculations ported unchanged from js/app.js so every page shows the same numbers as the prototype.
   Inputs (company price, KPI, peer groups ...) now come from the Django API instead of data.js. */
import { MEASURES } from '@/lib/roles';
import { num } from '@/lib/format';

export function rng(seed) { let x = seed >>> 0; return function () { x = (x * 1664525 + 1013904223) >>> 0; return x / 4294967296; }; }
export function seedOf(id) { let h = 7; for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0; return h; }

/* Deterministic sample series per company: price, volume, spread. `c` is a Company object from the API. */
export function series(c, n, salt) {
  const r = rng(seedOf(c.id) + (salt || 0));
  let p = c.price * 0.93;
  const out = [];
  for (let i = 0; i < n; i++) {
    p += (r() - 0.46) * c.price * 0.03;
    p = Math.max(c.price * 0.75, Math.min(c.price * 1.18, p));
    out.push({ p: p, v: c.vol30 / 30 * (0.35 + r() * 1.3), s: c.spread30 * (0.8 + r() * 0.45) });
  }
  const k = c.price / out[n - 1].p;
  out.forEach((x) => { x.p *= k; });
  return out;
}

export function fmtM(i, v) { return i === 0 ? num(v) : i === 1 ? Number(v).toFixed(1) : i === 2 ? Number(v).toFixed(1) + '%' : Number(v).toFixed(2) + '%'; }

/* Peer position of a company against an anonymised peer group (30-day figures). `k30` = KPI['30d'] */
export function position(k30, g) {
  return MEASURES.map((m, i) => {
    const v = k30[m[2]], med = g.median[i], d = (v - med) / med;
    let st;
    if (Math.abs(d) < 0.1) st = ['inf', 'Near median'];
    else { const up = d > 0; st = [(i === 1 ? !up : up) ? 'ok' : 'warn', up ? 'Above median' : 'Below median']; }
    return { label: m[0], unit: m[1], value: fmtM(i, v), median: fmtM(i, med), range: g.range[i], state: st };
  });
}

/* SVG path for the little sparkline on the KPI cards (same maths as App.spark). */
export function sparkPath(vals) {
  const w = 70, h = 24, mn = Math.min.apply(null, vals), mx = Math.max.apply(null, vals), rg = (mx - mn) || 1;
  return vals.map((v, i) => (i ? 'L' : 'M') + (i * w / (vals.length - 1)).toFixed(1) + ',' + (h - 2 - (v - mn) / rg * (h - 4)).toFixed(1)).join('');
}
