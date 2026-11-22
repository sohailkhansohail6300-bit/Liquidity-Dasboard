'use client';
import { useEffect, useRef, useState } from 'react';
import { useApp } from '@/components/AppProvider';
import { sparkPath } from '@/lib/derive';

export function Badge({ kind, children }) { return <span className={'bd ' + kind}>{children}</span>; }

export function Chips({ ids }) {
  const { companyMap } = useApp();
  if (!ids || !ids.length) return <span className="text-cap">&mdash;</span>;
  return (
    <span className="chip-list">
      {ids.map((i) => { const n = (companyMap[i] || { name: i }).name; return <span className="chip" key={i} title={n}>{n}</span>; })}
    </span>
  );
}

export function Spark({ vals }) {
  return (
    <svg viewBox="0 0 70 24" className="h-6 w-16" aria-hidden="true"><path d={sparkPath(vals)} fill="none" strokeWidth="1.6" className="c-spark" /></svg>
  );
}

export function Logo({ size = 28 }) {
  return (
    <>
      <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false"><path d="M16 3 30 29H2z" fill="#F2B705" /><path d="M16 12 21.5 23h-11z" fill="#0A1220" /></svg>
      <span className="text-sm font-semibold tracking-widest">DELTABLOCK</span>
    </>
  );
}

/* Dialog / drawer. Same markup + classes as the prototype's ".modal(.open)"; closes on Escape and on a click on the backdrop. */
export function Modal({ id, open, onClose, labelledBy, className, children }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!open) return undefined;
    const f = ref.current && ref.current.querySelector('input:not([type=hidden]),select,textarea');
    const t = setTimeout(() => { if (f) f.focus(); }, 30);
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    return () => { clearTimeout(t); document.removeEventListener('keydown', onKey); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);
  return (
    <div id={id} ref={ref} className={'modal' + (className ? ' ' + className : '') + (open ? ' open' : '')} role="dialog" aria-modal="true" aria-labelledby={labelledBy}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      {children}
    </div>
  );
}

const MOON = (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z" /></svg>
);
const SUN = (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
);

/* Light/dark theme button. The theme itself is applied before first paint by the inline script in app/layout.js
   (same storage key as the prototype: dbt-theme-v2, a non-sensitive UI preference). */
export function ThemeToggle() {
  const [dark, setDark] = useState(null);
  useEffect(() => { setDark(document.documentElement.dataset.theme === 'dark'); }, []);
  const label = dark === null ? 'Toggle dark mode' : dark ? 'Switch to light mode' : 'Switch to dark mode';
  return (
    <button type="button" data-theme-toggle className="btn !p-2" aria-label={label} title={label} aria-pressed={dark === null ? undefined : String(dark)}
      onClick={() => {
        const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
        document.documentElement.dataset.theme = next;
        try { localStorage.setItem('dbt-theme-v2', next); } catch (e) { /* ignore */ }
        setDark(next === 'dark');
      }}>
      <span className="t-moon">{MOON}</span><span className="t-sun">{SUN}</span>
    </button>
  );
}

/* Fixed top-right theme button used on the sign-in style pages. */
export function ThemeCorner() { return <div className="fixed right-4 top-4 z-10"><ThemeToggle /></div>; }

export function DocTitle({ title }) {
  useEffect(() => { document.title = title + ' | Deltablock'; }, [title]);
  return null;
}

/* Left brand panel + form column shared by Login and Create account. */
export function AuthShell({ children }) {
  const mark = (s) => (<svg width={s} height={s} viewBox="0 0 32 32" aria-hidden="true"><path d="M16 3 30 29H2z" fill="#F2B705" /><path d="M16 12 21.5 23h-11z" fill="#0A1220" /></svg>);
  return (
    <>
      <ThemeCorner />
      <div className="auth-shell grid min-h-screen lg:grid-cols-[0.9fr_1.1fr]">
        <div className="hidden flex-col justify-between auth-panel p-10 text-white lg:flex xl:p-14">
          <div className="flex items-center gap-3">{mark(30)}<span className="font-semibold tracking-[.14em]">DELTABLOCK</span></div>
          <div>
            <div className="mb-8 w-72">
              <svg viewBox="0 0 320 240" className="w-full" aria-hidden="true"><rect x="40" y="30" width="170" height="110" rx="14" fill="#fff" opacity=".1" /><path d="M55 120 90 90l30 20 40-45 35 25" fill="none" stroke="#F2B705" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" /><rect x="60" y="150" width="14" height="40" rx="3" fill="#fff" opacity=".25" /><rect x="84" y="136" width="14" height="54" rx="3" fill="#fff" opacity=".25" /><rect x="108" y="120" width="14" height="70" rx="3" fill="#F2B705" opacity=".8" /><rect x="132" y="142" width="14" height="48" rx="3" fill="#fff" opacity=".25" /></svg>
            </div>
            <h2 className="max-w-md text-3xl font-semibold leading-tight">Liquidity insight for listed companies.</h2>
            <p className="mt-3 max-w-md text-[#AEB8CE]">Track volume, spread and participation in one secure workspace.</p>
          </div>
        </div>
        <div className="auth-form-stage grid place-items-center p-5 sm:p-8 lg:p-10">
          <div className="auth-mobile-brand flex items-center gap-2">{mark(30)}<b className="text-sm tracking-[.14em]">DELTABLOCK</b></div>
          <div className="auth-form-card w-full max-w-md">{children}</div>
        </div>
      </div>
    </>
  );
}
