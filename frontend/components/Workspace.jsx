'use client';
import { useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useApp } from '@/components/AppProvider';
import { Logo, ThemeToggle, DocTitle } from '@/components/ui';
import { NAV, ROLES } from '@/lib/roles';
import { num } from '@/lib/format';

function Denied({ role }) {
  const r = ROLES[role];
  return (
    <div className="card mx-auto mt-10 max-w-lg p-8 text-center">
      <h1 className="text-xl font-semibold">This page is not part of your access</h1>
      <p className="mt-2 text-sm text-mut">{r.label} accounts do not include this page{role === 'guest' ? ' (guests have read-only access to Overview, Market activity, Trade history, Peer comparison, Reports and Company profile only)' : ''}. Your menu shows everything you can open.</p>
      <Link className="btn btn-p mt-6" href={r.home}>Go to {r.homeName}</Link>
    </div>
  );
}
function NoCompany() {
  return (
    <div className="card mx-auto mt-10 max-w-lg p-8 text-center">
      <h1 className="text-xl font-semibold">No company access yet</h1>
      <p className="mt-2 text-sm text-mut">Your account is not linked to a company. Contact your administrator.</p>
      <Link className="btn btn-p mt-6" href="/login">Back to sign in</Link>
    </div>
  );
}
function NoData({ co, role }) {
  const vals = [];
  if (co.price != null) vals.push(['Reference price', <>&euro;{Number(co.price).toFixed(3)}</>]);
  if (co.vol30 != null) vals.push(['Volume, last 30 days', num(co.vol30) + ' shares']);
  if (co.spread30 != null) vals.push(['Average spread, last 30 days', Number(co.spread30).toFixed(1) + ' bps']);
  return (
    <div className="card mx-auto mt-10 max-w-xl p-8 text-center">
      <span className="bd dr">Not available yet</span>
      <h1 className="mt-3 text-xl font-semibold">No market data for {co.name} yet</h1>
      <p className="mt-2 text-sm text-mut">No trade or reference-price feed has been connected for this company, so no figures are shown rather than made-up ones.</p>
      {vals.length ? (
        <>
          <dl className="mx-auto mt-5 grid max-w-sm gap-2 text-left text-sm">
            {vals.map((v) => (<div className="flex justify-between gap-4 border-t pt-2" key={v[0]}><dt className="text-cap">{v[0]}</dt><dd className="mono">{v[1]}</dd></div>))}
          </dl>
          <p className="mt-2 text-xs text-cap">Values entered by an administrator when the company was added.</p>
        </>
      ) : null}
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        {role === 'admin'
          ? (<><Link className="btn btn-p" href="/data-health">Open Data health</Link> <Link className="btn" href="/companies">Back to Companies</Link></>)
          : <Link className="btn btn-p" href={'/tickets?new=1&subject=' + encodeURIComponent('Market data for ' + co.name)}>Ask support</Link>}
      </div>
    </div>
  );
}

/* Page frame for every signed-in page: sidebar, top bar, role / company gates. Replaces App.mount()/shell() from js/app.js.
   The gates here only decide what to *show*; the API enforces the same rules and is authoritative. */
export default function Workspace({ page, navFor, title, crumb, roles, scoped, needsData, children }) {
  const app = useApp();
  const router = useRouter();
  const navToggle = useRef(null);

  useEffect(() => { if (!app.loading && !app.me) router.replace('/login'); }, [app.loading, app.me, router]);
  useEffect(() => { if (navToggle.current) navToggle.current.checked = false; }, [app.pathname]);

  if (app.loading || !app.me) return <DocTitle title={title || ''} />;

  const { me, co, allowed } = app;
  const role = me.role;
  const r = ROLES[role];
  const ok = !roles || roles.indexOf(role) >= 0;
  const scopedCo = scoped && co;
  let activeHref = navFor || '/' + page;
  if (role === 'admin' && scopedCo) activeHref = '/companies';

  const counts = { '/access-requests': app.counts.accessRequestsPending, '/profile-reviews': app.counts.profileReviewsPending };
  const items = NAV[role].map((n) => {
    const on = n[0] === activeHref;
    const cnt = role === 'admin' ? (counts[n[0]] || 0) : 0;
    return (
      <Link key={n[0]} href={n[0]} className={on ? 'on' : ''} aria-current={on ? 'page' : undefined}>
        {n[1]}{cnt ? <span className="navcount" data-count={n[0]}>{cnt}</span> : null}
      </Link>
    );
  });

  let body;
  if (!ok) body = <Denied role={role} />;
  else if (scoped && !co) body = <NoCompany />;
  else if (needsData && co && !co.hasData) body = <NoData co={co} role={role} />;
  else body = children;

  const manager = role !== 'admin' && role !== 'guest' ? (me.manages.length ? ' · manager' : ' · team member') : '';

  return (
    <div id="root">
      <DocTitle title={title || ''} />
      <input id="responsive-nav" ref={navToggle} className="sr-only" type="checkbox" /><label className="nav-backdrop" htmlFor="responsive-nav" aria-label="Close navigation" />
      <div className="flex min-h-screen">
        <aside className="side responsive-side flex w-52 shrink-0 flex-col" aria-label="Main">
          <Link className="flex h-16 items-center gap-3 border-b border-white/10 px-5 text-white" href={r.home} aria-label="DeltaBlock home"><Logo size={28} /></Link>
          <nav className="flex-1 py-4">{items}</nav>
          {(role === 'client' || role === 'multi') ? (
            <div className="m-3 rounded-xl bg-white/5 p-4 text-xs text-[#AEB8CE]">Need help? <Link href="/tickets?new=1" className="!m-0 !inline !p-0 text-white underline">Open a support ticket</Link>.</div>
          ) : null}
        </aside>
        <div className="min-w-0 flex-1">
          <header className="flex h-14 items-center border-b bg-surf px-6">
            <label className="btn mobile-menu" htmlFor="responsive-nav" aria-label="Open navigation"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg></label>
            <div className="hidden items-center gap-2 text-sm text-cap sm:flex">
              <span>{r.area}</span>
              {role === 'admin' && scopedCo ? (<><span>/</span><Link className="hover:underline" href="/companies">Companies</Link><span>/</span><span className="crumb-co">{co.name}</span></>) : null}
              <span>/</span><span className="font-medium text-ink">{crumb || title}</span>
            </div>
            <div className="ml-auto flex items-center gap-3">
              {scopedCo ? (allowed.length > 1 ? (
                <label className="hidden items-center gap-2 text-xs text-mut sm:flex">Company{' '}
                  <select id="company-switch" className="inp !w-40 !py-1.5" aria-label="Company" value={co.id}
                    onChange={(e) => { const v = e.target.value; if (!app.setCompany(v)) { app.toast('You do not have access to that company.', 'err'); return; } app.toast('Showing ' + app.companyMap[v].name); }}>
                    {allowed.map((id) => <option key={id} value={id}>{app.companyMap[id].name}</option>)}
                  </select>
                </label>
              ) : <span className="chip hidden sm:inline-flex">{co.name}</span>) : null}
              <ThemeToggle />
              <a href="/login" className="text-sm text-mut hover:underline" onClick={async (e) => { e.preventDefault(); await app.signOut(); router.push('/login'); }}>Sign out</a>
              <Link href="/account" className="flex items-center gap-2 border-l pl-3 hover:opacity-80" title="My account" aria-label={'My account. Signed in as ' + me.name + ', ' + r.label}>
                <span className="grid h-8 w-8 shrink-0 place-items-center" style={{ color: '#F2B705' }} aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="8" r="3.25" /><path d="M5.5 20c.35-3.45 2.75-5.5 6.5-5.5s6.15 2.05 6.5 5.5" /></svg></span>
                <div className="hidden leading-tight sm:block"><div className="text-sm font-semibold text-ink">{me.name}</div><div className="text-xs text-cap">{r.label}{manager}</div></div>
              </Link>
            </div>
          </header>
          <main id="main" className="mx-auto max-w-[1280px] p-6 md:p-8">{body}</main>
        </div>
      </div>
      <div id="overlays" />
    </div>
  );
}
