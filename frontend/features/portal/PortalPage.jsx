'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import Workspace from '@/components/Workspace';
import { useApp } from '@/components/AppProvider';
import { Badge, Chips } from '@/components/ui';
import { useLoad } from '@/hooks/useLoad';
import { api, qstr } from '@/lib/api';
import { fmtDate, fmtTradeDt, num } from '@/lib/format';

const TITLES = {
  admin: ['Admin overview', ['admin']],
  market: ['Market activity', ['client', 'multi', 'guest', 'admin']],
  trades: ['Trade history', ['client', 'multi', 'guest', 'admin']],
  comparison: ['Peer comparison', ['client', 'multi', 'guest', 'admin']],
  reports: ['Reports', ['client', 'multi', 'guest', 'admin']],
  accounting: ['Statements', ['client', 'multi', 'admin']],
  subscription: ['Subscription', ['client', 'multi', 'admin']],
  company: ['Company profile', ['client', 'multi', 'guest', 'admin']],
  team: ['Team', ['client', 'multi', 'admin']],
  companies: ['Companies', ['client', 'multi', 'admin']],
  tickets: ['Support', ['client', 'multi', 'admin']],
  ticket: ['Support ticket', ['client', 'multi', 'admin']],
  account: ['My account', ['client', 'multi', 'guest', 'admin']],
  'signup-links': ['Client sign-up links', ['admin']],
  'access-requests': ['Access requests', ['admin']],
  'profile-reviews': ['Profile reviews', ['admin']],
  users: ['Users', ['admin']],
  'admin-subscriptions': ['Subscriptions', ['admin']],
  'data-health': ['Data health', ['admin']],
  'access-log': ['Access log', ['admin']],
  wireframes: ['Screen map', ['admin']],
};

async function loadPage(slug, companyId, ticketId, filter, page) {
  switch (slug) {
    case 'admin': return api.get('/admin/counts/');
    case 'companies': return api.get('/companies/');
    case 'market': return api.get('/companies/' + companyId + '/kpi/');
    case 'trades': return api.get('/companies/' + companyId + '/trades/' + qstr({ q: filter }));
    case 'comparison': return Promise.all([api.get('/companies/' + companyId + '/kpi/'), api.get('/peer-groups/')]);
    case 'reports': return api.get('/reports/');
    case 'accounting': return api.get('/companies/' + companyId + '/statements/');
    case 'subscription': return api.get('/subscriptions/');
    case 'company': return api.get('/companies/' + companyId + '/profile-reviews/');
    case 'team': return api.get('/companies/' + companyId + '/team/');
    case 'tickets':
    case 'ticket': return api.get('/tickets/');
    case 'ticket-detail': return api.get('/tickets/' + encodeURIComponent(ticketId) + '/');
    case 'signup-links': return api.get('/admin/signup-links/');
    case 'access-requests': return api.get('/admin/access-requests/');
    case 'profile-reviews': return api.get('/admin/profile-reviews/');
    case 'users': return api.get('/admin/users/');
    case 'admin-subscriptions': return Promise.all([api.get('/companies/'), api.get('/subscriptions/')]);
    case 'data-health': return api.get('/admin/feeds/');
    case 'access-log': return api.get('/admin/access-log/' + qstr({ q: filter, page, size: 10 }));
    default: return null;
  }
}

function Table({ columns, rows, empty = 'No records to show.' }) {
  if (!rows || !rows.length) return <div className="card p-5 text-sm text-mut">{empty}</div>;
  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead><tr className="border-b text-xs text-cap">{columns.map((col) => <th className="px-4 py-3 font-medium" key={col.key}>{col.label}</th>)}</tr></thead>
        <tbody>
          {rows.map((row, i) => <tr className="border-b last:border-b-0" key={String(row.id || row.ref || row.document || row.email || 'row') + '-' + i}>
            {columns.map((col) => <td className="px-4 py-3 align-top" key={col.key}>{col.render ? col.render(row) : (row[col.key] == null || row[col.key] === '' ? '—' : row[col.key])}</td>)}
          </tr>)}
        </tbody>
      </table>
    </div>
  );
}

function SectionTitle({ title, description, children }) {
  return <div className="mb-6 flex flex-wrap items-end justify-between gap-3"><div><h1 className="page-title">{title}</h1>{description ? <p className="mt-2 text-sm text-mut">{description}</p> : null}</div>{children}</div>;
}

function StateBadge({ value }) {
  const status = Array.isArray(value) ? value : [value === 'active' ? 'ok' : value === 'pending' ? 'warn' : 'dr', value];
  return <Badge kind={status[0]}>{status[1]}</Badge>;
}

export default function PortalPage({ ticketId }) {
  const pathname = usePathname();
  const app = useApp();
  const routeSlug = pathname.split('/').filter(Boolean)[0] || '';
  const slug = routeSlug === 'ticket' && ticketId ? 'ticket-detail' : routeSlug;
  const [filter, setFilter] = useState('');
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [tick, setTick] = useState(0);
  const [form, setForm] = useState({});
  const config = TITLES[routeSlug] || TITLES.ticket;
  const title = config[0];
  const companyId = app.co ? app.co.id : '';
  const { data, error, loading } = useLoad(
    () => loadPage(slug, companyId, ticketId, filter, page),
    [slug, companyId, ticketId, filter, page, tick],
  );

  async function submit(action, successMessage) {
    setBusy(true);
    try {
      await action();
      app.toast(successMessage || 'Saved');
      setForm({});
      setTick((value) => value + 1);
    } catch (e) {
      app.toast(e.message || 'The request could not be completed.', 'err');
    } finally {
      setBusy(false);
    }
  }

  const commonProps = { page: routeSlug, title, roles: config[1] };
  if (['market', 'trades', 'comparison', 'accounting', 'subscription', 'company', 'team'].includes(routeSlug)) {
    commonProps.scoped = true;
    commonProps.needsData = ['market', 'trades', 'comparison'].includes(routeSlug);
  }

  let content = null;
  if (app.loading || !app.me) {
    content = null;
  } else if (loading) {
    content = <div className="card p-5 text-sm text-mut" role="status">Loading {title.toLowerCase()}…</div>;
  } else if (error) {
    content = <div className="card border-l-4 border-red-500 p-5 text-sm" role="alert"><b>Could not load this page.</b><p className="mt-1 text-mut">{error.message}</p><button className="btn btn-s mt-3" type="button" onClick={() => setTick((value) => value + 1)}>Try again</button></div>;
  } else {
    content = renderContent({
      slug, data, app, companyId, ticketId, filter, setFilter, page, setPage,
      form, setForm, busy, submit,
    });
  }

  return <Workspace {...commonProps}>{content}</Workspace>;
}

function renderContent(ctx) {
  const { slug, data, app, companyId, filter, setFilter, page, setPage, form, setForm, busy, submit } = ctx;
  const co = app.co;
  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const field = (key, label, type = 'text', value = form[key] || '') => (
    <label className="block text-sm" key={key}><span className="lbl">{label}</span><input className="inp" type={type} value={value} onChange={(e) => set(key, e.target.value)} /></label>
  );
  const button = (label, action, kind = 'btn btn-p') => <button className={kind} type="button" disabled={busy} onClick={() => submit(action)}>{busy ? 'Saving…' : label}</button>;
  const decisionButtons = (url, id) => <div className="flex gap-2">{button('Approve', () => api.post(url + id + '/decision/', { decision: 'approve', note: '' }), 'btn btn-s')}{button('Reject', () => api.post(url + id + '/decision/', { decision: 'reject', note: '' }), 'btn btn-s')}</div>;

  switch (slug) {
    case 'admin':
      return <><SectionTitle title="Admin overview" description="Review and manage the Deltablock workspace." /><div className="grid gap-4 sm:grid-cols-2"><Link className="card p-5 hover:border-current" href="/access-requests"><div className="text-sm text-cap">Pending access requests</div><div className="metric mt-2">{data.accessRequestsPending}</div><span className="text-sm underline">Review requests</span></Link><Link className="card p-5 hover:border-current" href="/profile-reviews"><div className="text-sm text-cap">Pending profile reviews</div><div className="metric mt-2">{data.profileReviewsPending}</div><span className="text-sm underline">Review changes</span></Link></div></>;
    case 'companies':
      return <><SectionTitle title="Companies" description="Companies available to your account." /><Table columns={[
        { key: 'name', label: 'Company', render: (r) => <Link className="font-medium underline" href="/dashboard">{r.name}</Link> },
        { key: 'code', label: 'Ticker' }, { key: 'exch', label: 'Exchange' },
        { key: 'price', label: 'Reference price', render: (r) => r.price == null ? '—' : '€' + Number(r.price).toFixed(3) },
        { key: 'feed', label: 'Data feed', render: (r) => <StateBadge value={r.feed} /> },
      ]} rows={data} /></>;
    case 'market': {
      const k = data.kpi['30d'] || {};
      const s = data.kpi.since || {};
      return <><SectionTitle title="Market activity" description={'Liquidity and participation metrics for ' + co.name + '.'} /><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[['Time in market', k.tim, '%'], ['Volume traded', num(k.vol), ' shares'], ['Average spread', k.spr, ' bps'], ['Market turnover', k.turn, '%']].map(([label, value, unit]) => <div className="card p-5" key={label}><div className="metric-label">{label}</div><div className="metric mt-2">{value}{unit}</div></div>)}</div><div className="card mt-5 p-5"><h2 className="font-semibold">Since contract start</h2><p className="mt-2 text-sm text-mut">{s.vol ? num(s.vol) + ' shares traded · ' + s.share + '% Deltablock contribution' : 'No contract data available.'}</p><p className="mt-1 text-xs text-cap">Contract start: {fmtDate(data.contractStartIso)}</p></div></>;
    }
    case 'trades':
      return <><SectionTitle title="Trade history" description={'Executed trades for ' + co.name + '.'}><input aria-label="Search trades" className="inp !w-64" placeholder="Search reference or venue" value={filter} onChange={(e) => setFilter(e.target.value)} /></SectionTitle><Table columns={[
        { key: 'executedAt', label: 'Executed', render: (r) => fmtTradeDt(r.executedAt) },
        { key: 'side', label: 'Side' }, { key: 'shares', label: 'Shares', render: (r) => num(r.shares) },
        { key: 'price', label: 'Price', render: (r) => '€' + Number(r.price).toFixed(3) },
        { key: 'value', label: 'Value', render: (r) => '€' + Number(r.value).toLocaleString('en-GB') },
        { key: 'venue', label: 'Venue' },
      ]} rows={data.results} empty="No trades match this search." /><p className="mt-3 text-xs text-cap">{data.total} total stored trades</p></>;
    case 'comparison': {
      const k = data[0].kpi['30d'];
      return <><SectionTitle title="Peer comparison" description={'Anonymised market benchmarks for ' + co.name + ', last 30 days.'} /><Table columns={[
        { key: 'name', label: 'Peer group' }, { key: 'n', label: 'Peers' },
        ...['Average daily volume', 'Average spread', 'Time in market', 'Turnover'].map((label, i) => ({ key: 'm' + i, label, render: (r) => <span>{r.median[i]}<small className="ml-1 text-cap">{['shares', 'bps', '%', '%'][i]}</small></span> })),
      ]} rows={data[1].map((r) => ({ ...r, n: r.n, m0: r.median[0] }))} /><p className="mt-3 text-xs text-cap">Your 30-day values: {num(k.vol)} shares · {k.spr} bps spread · {k.tim}% time in market · {k.turn}% turnover.</p></>;
    }
    case 'reports':
      return <><SectionTitle title="Reports" description="Published liquidity and market reports." /><Table columns={[
        { key: 'title', label: 'Report' }, { key: 'period', label: 'Period' },
        { key: 'publishedIso', label: 'Published', render: (r) => fmtDate(r.publishedIso) },
        { key: 'href', label: 'Download', render: (r) => <a className="underline" href={r.href} target="_blank" rel="noreferrer">Open PDF</a> },
      ]} rows={data} /></>;
    case 'accounting':
      return <><SectionTitle title="Statements" description={'Billing statements for ' + co.name + '.'} /><Table columns={[
        { key: 'document', label: 'Document' }, { key: 'period', label: 'Period' },
        { key: 'issuedIso', label: 'Issued', render: (r) => fmtDate(r.issuedIso) },
        { key: 'amount', label: 'Amount', render: (r) => '€' + Number(r.amount).toFixed(2) },
        { key: 'statusLabel', label: 'Status', render: (r) => <StateBadge value={[r.statusKind, r.statusLabel]} /> },
      ]} rows={data} /></>;
    case 'subscription': {
      const sub = data[companyId];
      return <><SectionTitle title="Subscription" description={'Contract details for ' + co.name + '.'} />{sub ? <div className="card p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-lg font-semibold">{sub.plan}</h2><p className="mt-1 text-sm text-mut">{sub.term}</p></div><StateBadge value={sub.status} /></div><dl className="mt-5 grid gap-4 sm:grid-cols-3 text-sm"><div><dt className="text-cap">Start date</dt><dd>{fmtDate(sub.startIso)}</dd></div><div><dt className="text-cap">End date</dt><dd>{fmtDate(sub.endIso)}</dd></div><div><dt className="text-cap">Renewal date</dt><dd>{fmtDate(sub.renewIso)}</dd></div></dl><p className="mt-5 text-sm text-mut">{sub.autoRenew}</p><h3 className="mt-5 font-semibold">Contracted services</h3><ul className="mt-2 divide-y">{sub.services.map(([name, scope]) => <li className="py-3" key={name}><b className="text-sm">{name}</b><p className="text-sm text-mut">{scope}</p></li>)}</ul></div> : null}</>;
    }
    case 'company':
      return <><SectionTitle title="Company profile" description="Approved company information and profile review status." /><div className="card p-5"><dl className="grid gap-4 sm:grid-cols-2">{[['Legal name', co.legal], ['Exchange', co.exch], ['Ticker', co.code], ['Shares outstanding', co.shares], ['Free float', co.float], ['Insiders', co.insiders], ['Institutions', co.institutions], ['Contact email', co.email], ['Phone', co.phone], ['Address', co.address]].map(([label, value]) => <div key={label}><dt className="text-xs text-cap">{label}</dt><dd className="mt-1 text-sm">{value || '—'}</dd></div>)}</dl></div>{data.pending ? <div className="card mt-5 p-5"><h2 className="font-semibold">Profile review pending</h2><p className="mt-2 text-sm text-mut">Submitted {fmtDate(data.pending.submittedOnIso)}</p>{app.can.editProfile(companyId) ? button('Withdraw request', () => api.del('/companies/' + companyId + '/profile-reviews/pending/')) : null}</div> : null}{app.can.editProfile(companyId) ? <form className="card mt-5 grid gap-4 p-5 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); const values = Object.fromEntries(['legal', 'exch', 'shares', 'float', 'insiders', 'institutions', 'email', 'phone', 'address'].map((k) => [k, form[k] === undefined ? co[k === 'legal' ? 'legal' : k === 'exch' ? 'exch' : k] || '' : form[k]])); submit(() => api.post('/companies/' + companyId + '/profile-reviews/', { values }), 'Profile change submitted for review'); }}><h2 className="font-semibold sm:col-span-2">Request a profile change</h2>{[['legal', 'Legal name'], ['exch', 'Exchange'], ['shares', 'Shares outstanding'], ['float', 'Free float'], ['insiders', 'Insiders'], ['institutions', 'Institutions'], ['email', 'Contact email'], ['phone', 'Phone'], ['address', 'Address']].map(([key, label]) => field(key, label, 'text', form[key] === undefined ? co[key] || '' : form[key]))}<button className="btn btn-p sm:col-span-2" disabled={busy}>Submit for review</button></form> : null}</>;
    case 'team':
      return <><SectionTitle title="Team" description={'People who can access ' + co.name + '.'} /><div className="card mb-5 p-5"><b className="text-sm">Company managers</b><p className="mt-1 text-sm text-mut">{data.managers.join(', ') || 'No active managers listed.'}</p></div><Table columns={[
        { key: 'name', label: 'Name' }, { key: 'email', label: 'Email' },
        { key: 'kind', label: 'Type' }, { key: 'companies', label: 'Companies', render: (r) => <Chips ids={r.companies} /> },
        { key: 'status', label: 'Status', render: (r) => <StateBadge value={r.status} /> },
      ]} rows={data.members} />{app.can.manage(companyId) ? <form className="card mt-5 grid gap-4 p-5 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); submit(() => api.post('/team/invitations/', { name: form.name || '', email: form.email || '', type: form.type || 'colleague', companies: [companyId] }), 'Invitation created'); }}><h2 className="font-semibold sm:col-span-2">Invite a team member</h2>{field('name', 'Name')} {field('email', 'Work email', 'email')}<label className="block text-sm"><span className="lbl">Access type</span><select className="inp" value={form.type || 'colleague'} onChange={(e) => set('type', e.target.value)}><option value="colleague">Colleague</option><option value="guest">Guest</option></select></label><button className="btn btn-p self-end" disabled={busy}>Create invitation</button></form> : null}</>;
    case 'tickets':
      return <><SectionTitle title={app.me.role === 'admin' ? 'Support tickets' : 'Support'} description="Track support conversations and requests." />{app.me.role !== 'admin' && app.me.role !== 'guest' ? <form className="card mb-5 grid gap-4 p-5 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); submit(() => api.post('/tickets/', { subject: form.subject || '', company: companyId, message: form.message || '' }), 'Ticket created'); }}><h2 className="font-semibold sm:col-span-2">Open a support ticket</h2>{field('subject', 'Subject')}<label className="block text-sm sm:col-span-2"><span className="lbl">Message</span><textarea className="inp min-h-24" value={form.message || ''} onChange={(e) => set('message', e.target.value)} /></label><button className="btn btn-p sm:col-span-2" disabled={busy}>Send ticket</button></form> : null}<Table columns={[
        { key: 'id', label: 'Ticket', render: (r) => <Link className="underline" href={'/ticket/' + encodeURIComponent(r.id)}>{r.id}</Link> },
        { key: 'subject', label: 'Subject' }, { key: 'company', label: 'Company' },
        { key: 'by', label: 'Opened by' }, { key: 'status', label: 'Status', render: (r) => <StateBadge value={r.status} /> },
        { key: 'updatedLabel', label: 'Updated' },
      ]} rows={data} /></>;
    case 'ticket-detail': {
      const t = data;
      return <><SectionTitle title={t.subject} description={t.id + ' · ' + t.company}><Link className="btn btn-s" href="/tickets">Back to tickets</Link></SectionTitle><div className="card mb-5 divide-y">{t.messages.map((m, i) => <article className="py-4 first:pt-0 last:pb-0" key={i}><div className="flex justify-between gap-3 text-sm"><b>{m.name}</b><time className="text-cap">{m.atLabel || m.at}</time></div><p className="mt-2 whitespace-pre-wrap text-sm">{m.text}</p></article>)}</div>{app.me.role === 'admin' || (app.me.role !== 'guest' && app.me.allowed.includes(t.company)) ? <form className="card grid gap-3 p-5" onSubmit={(e) => { e.preventDefault(); submit(() => api.post('/tickets/' + encodeURIComponent(t.id) + '/messages/', { text: form.message || '' }), 'Reply sent'); }}><label className="block text-sm"><span className="lbl">Reply</span><textarea className="inp min-h-24" value={form.message || ''} onChange={(e) => set('message', e.target.value)} /></label><button className="btn btn-p justify-self-start" disabled={busy}>Send reply</button></form> : null}</>;
    }
    case 'signup-links':
      return <><SectionTitle title="Client sign-up links" description="Create and review company invitations." /><form className="card mb-5 grid gap-4 p-5 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); submit(() => api.post('/admin/signup-links/', { companies: form.companies || [], days: Number(form.days || 14) }), 'Sign-up link created'); }}><h2 className="font-semibold sm:col-span-2">Create a sign-up link</h2><label className="block text-sm"><span className="lbl">Companies</span><select multiple className="inp min-h-24" value={form.companies || []} onChange={(e) => set('companies', Array.from(e.target.selectedOptions).map((o) => o.value))}>{app.companies.map((c) => <option value={c.id} key={c.id}>{c.name}</option>)}</select></label>{field('days', 'Valid for days', 'number', form.days || '14')}<button className="btn btn-p sm:col-span-2" disabled={busy}>Create link</button></form><Table columns={[
        { key: 'id', label: 'Link' }, { key: 'token', label: 'Token' },
        { key: 'companies', label: 'Companies', render: (r) => <Chips ids={r.companies} /> },
        { key: 'expiresIso', label: 'Expires', render: (r) => fmtDate(r.expiresIso) },
        { key: 'state', label: 'Status', render: (r) => <StateBadge value={r.state} /> },
        { key: 'action', label: 'Action', render: (r) => r.state === 'unused' ? button('Revoke', () => api.post('/admin/signup-links/' + r.id + '/revoke/', {}), 'btn btn-s') : '—' },
      ]} rows={data} /></>;
    case 'access-requests':
      return <><SectionTitle title="Access requests" description="Review requests for client access." /><Table columns={[
        { key: 'name', label: 'Name' }, { key: 'email', label: 'Email' }, { key: 'company', label: 'Company' },
        { key: 'message', label: 'Message' }, { key: 'dateIso', label: 'Received', render: (r) => fmtDate(r.dateIso) },
        { key: 'status', label: 'Status', render: (r) => <StateBadge value={r.status} /> },
        { key: 'action', label: 'Action', render: (r) => r.status === 'pending' ? decisionButtons('/admin/access-requests/', r.id) : '—' },
      ]} rows={data} /></>;
    case 'profile-reviews':
      return <><SectionTitle title="Profile reviews" description="Approve or reject client-submitted company changes." /><Table columns={[
        { key: 'id', label: 'Request' }, { key: 'company', label: 'Company' }, { key: 'by', label: 'Submitted by', render: (r) => r.by.name + ' · ' + r.by.email },
        { key: 'submittedOnIso', label: 'Submitted', render: (r) => fmtDate(r.submittedOnIso) }, { key: 'status', label: 'Status', render: (r) => <StateBadge value={r.status} /> },
        { key: 'changes', label: 'Changes', render: (r) => Object.entries(r.changes).map(([k, v]) => <div key={k}>{k}: {v.from} → {v.to}</div>) },
        { key: 'action', label: 'Action', render: (r) => r.status === 'pending' ? decisionButtons('/admin/profile-reviews/', r.id) : '—' },
      ]} rows={data} /></>;
    case 'users':
      return <><SectionTitle title="Users" description="Account and company-access overview." /><Table columns={[
        { key: 'name', label: 'Name' }, { key: 'email', label: 'Email' }, { key: 'kind', label: 'Type' },
        { key: 'companies', label: 'Companies', render: (r) => <Chips ids={r.companies} /> },
        { key: 'manages', label: 'Manages', render: (r) => <Chips ids={r.manages} /> },
        { key: 'status', label: 'Status', render: (r) => <StateBadge value={r.status} /> },
        { key: 'ownerName', label: 'Account owner' },
      ]} rows={data} /></>;
    case 'admin-subscriptions': {
      const [companies, subs] = data;
      return <><SectionTitle title="Subscriptions" description="Review the current service contract for each company." /><Table columns={[
        { key: 'name', label: 'Company' },
        { key: 'plan', label: 'Plan', render: (r) => subs[r.id] && !subs[r.id].none ? subs[r.id].plan : 'Not assigned' },
        { key: 'term', label: 'Term', render: (r) => subs[r.id] && !subs[r.id].none ? subs[r.id].term : '—' },
        { key: 'renewIso', label: 'Renewal', render: (r) => fmtDate(subs[r.id] && subs[r.id].renewIso) },
        { key: 'status', label: 'Status', render: (r) => subs[r.id] ? <StateBadge value={subs[r.id].status} /> : '—' },
      ]} rows={companies} /><form className="card mt-5 grid gap-4 p-5 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); submit(() => api.put('/admin/subscriptions/' + form.company + '/', { plan: form.plan || 'Liquidity Essentials', term: form.term || 'Annual service', startIso: form.startIso, renewIso: form.renewIso, autoRenew: form.autoRenew || '', services: [] }), 'Subscription saved'); }}><h2 className="font-semibold sm:col-span-2">Edit a subscription</h2><label className="block text-sm"><span className="lbl">Company</span><select className="inp" value={form.company || companies[0]?.id || ''} onChange={(e) => set('company', e.target.value)}>{companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label className="block text-sm"><span className="lbl">Plan</span><select className="inp" value={form.plan || 'Liquidity Essentials'} onChange={(e) => set('plan', e.target.value)}>{['Liquidity Essentials', 'Liquidity Plus', 'Investor Relations'].map((p) => <option key={p}>{p}</option>)}</select></label>{field('term', 'Service term', 'text', form.term || 'Annual service')}{field('startIso', 'Start date', 'date')}{field('renewIso', 'Renewal date', 'date')}{field('autoRenew', 'Auto-renew text')}<button className="btn btn-p sm:col-span-2" disabled={busy}>Save subscription</button></form></>;
    }
    case 'data-health':
      return <><SectionTitle title="Data health" description="Latest status for market data feeds." /><Table columns={[
        { key: 'company', label: 'Company', render: (r) => app.companyMap[r.company]?.name || r.company },
        { key: 'name', label: 'Feed' }, { key: 'latest', label: 'Latest record' }, { key: 'expected', label: 'Expected interval' },
        { key: 'records', label: 'Records today', render: (r) => num(r.records) },
        { key: 'status', label: 'Status', render: (r) => <StateBadge value={r.status} /> },
      ]} rows={data} /></>;
    case 'access-log':
      return <><SectionTitle title="Access log" description="Search recent account access activity."><input className="inp !w-64" value={filter} placeholder="Search the access log" onChange={(e) => { setFilter(e.target.value); setPage(1); }} /></SectionTitle><Table columns={[
        { key: 'stamp', label: 'Time' }, { key: 'first', label: 'First name' }, { key: 'last', label: 'Last name' }, { key: 'email', label: 'Email' }, { key: 'company', label: 'Company' },
      ]} rows={data.results} /><div className="mt-4 flex items-center justify-between text-sm"><span>{num(data.filteredTotal)} matching of {num(data.total)}</span><div className="flex gap-2"><button className="btn btn-s" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button><span className="self-center">{page} / {data.pages}</span><button className="btn btn-s" disabled={page >= data.pages} onClick={() => setPage(page + 1)}>Next</button></div></div></>;
    case 'account':
      return <><SectionTitle title="My account" description="Update your personal details and password." /><form className="card grid gap-4 p-5 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); submit(() => api.patch('/auth/account/', { first: form.first ?? app.me.first, last: form.last ?? app.me.last, email: form.email ?? app.me.email }), 'Account updated'); }}><h2 className="font-semibold sm:col-span-2">Personal details</h2>{field('first', 'First name', 'text', form.first ?? app.me.first)}{field('last', 'Last name', 'text', form.last ?? app.me.last)}{field('email', 'Email', 'email', form.email ?? app.me.email)}<button className="btn btn-p sm:col-span-2" disabled={busy}>Save details</button></form><form className="card mt-5 grid gap-4 p-5 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); submit(() => api.post('/auth/password/change/', { current: form.current || '', next: form.next || '', confirm: form.confirm || '' }), 'Password changed'); }}><h2 className="font-semibold sm:col-span-2">Change password</h2>{field('current', 'Current password', 'password')}{field('next', 'New password', 'password')}{field('confirm', 'Confirm password', 'password')}<button className="btn btn-p sm:col-span-2" disabled={busy}>Change password</button></form></>;
    case 'wireframes':
      return <><SectionTitle title="Screen map" description="Available workspace routes by role." /><Table columns={[
        { key: 'role', label: 'Role' }, { key: 'routes', label: 'Pages', render: (r) => r.routes.map(([href, label]) => <Link className="mr-3 inline-block underline" key={href} href={href}>{label}</Link>) },
      ]} rows={Object.entries({
        Client: [['/dashboard', 'Overview'], ['/market', 'Market activity'], ['/trades', 'Trade history'], ['/comparison', 'Peer comparison'], ['/reports', 'Reports'], ['/accounting', 'Statements'], ['/subscription', 'Subscription'], ['/company', 'Company profile'], ['/team', 'Team'], ['/tickets', 'Support']],
        Admin: [['/admin', 'Admin overview'], ['/companies', 'Companies'], ['/signup-links', 'Sign-up links'], ['/access-requests', 'Access requests'], ['/profile-reviews', 'Profile reviews'], ['/users', 'Users'], ['/admin-subscriptions', 'Subscriptions'], ['/data-health', 'Data health'], ['/access-log', 'Access log'], ['/tickets', 'Support tickets']],
      }).map(([role, routes]) => ({ role, routes }))} /></>;
    default:
      return <div className="card p-5 text-sm text-mut">This workspace route is not available.</div>;
  }
}
