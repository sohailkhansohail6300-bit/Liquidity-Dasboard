/* Formatting helpers ported 1:1 from js/app.js (same output as the static prototype). */
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function num(n) { return Number(n).toLocaleString('en-GB'); }

/* "2026-10-04" -> "04 Oct 2026" (fixed month names so "Sep" is never rendered as "Sept" by newer ICU data). */
export function fmtDate(iso) {
  if (!iso) return '—';
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso));
  if (!m) return String(iso);
  return m[3] + ' ' + MON[+m[2] - 1] + ' ' + m[1];
}
export function addIso(iso, n) {
  const d = new Date(iso + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
export function isoLocal(d) {
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}
export function todayIso() { return isoLocal(new Date()); }
export function daysUntil(iso, todayDemo) { return Math.round((Date.parse(iso) - Date.parse(todayDemo)) / 86400000); }
export function initials(n) { return String(n).split(' ').map((x) => x[0]).slice(0, 2).join('').toUpperCase(); }
export function typeLabel(p) {
  return p.kind === 'admin' ? 'Admin' : p.kind === 'guest' ? 'Guest' : p.kind === 'colleague' ? 'Client · colleague' : (p.isOwner ? 'Client · account owner' : 'Client');
}
export function absUrl(rel) {
  try { return new URL(rel, window.location.href).href; } catch (e) { return rel; }
}
export function lc(v) { return String(v == null ? '' : v).trim().toLowerCase(); }
export function pad2(n) { return String(n).padStart(2, '0'); }
/* "2026-10-23T14:22:00" -> "23 Oct 2026 · 14:22" (day is not zero padded, as in the prototype's trade table). */
export function fmtTradeDt(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso);
  return m ? (+m[3]) + ' ' + MON[+m[2] - 1] + ' ' + m[1] + ' · ' + m[4] + ':' + m[5] : iso;
}
