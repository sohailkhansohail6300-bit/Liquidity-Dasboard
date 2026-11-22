'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useApp } from '@/components/AppProvider';
import { DocTitle, ThemeCorner } from '@/components/ui';
import { useQueryParams } from '@/hooks/useLoad';
import { ROLES } from '@/lib/roles';

export default function GuestInvitePage() {
  const app = useApp();
  const router = useRouter();
  const q = useQueryParams();
  const t = q ? q.get('t') : undefined;
  const [info, setInfo] = useState(undefined);
  const [sample, setSample] = useState(null);
  const [f, setF] = useState({ name: '', password: '', confirm: '' });
  const [err, setErr] = useState('');

  useEffect(() => {
    if (q === null) return;
    if (!t) { setInfo({ state: 'invalid' }); return; }
    api.get('/signup/' + encodeURIComponent(t) + '/', { quiet401: true }).then((r) => {
      setInfo(r);
      if (r.state === 'open') setF((x) => ({ ...x, name: r.name || '' }));
    }, () => setInfo({ state: 'invalid' }));
  }, [q, t]);

  const invalid = info && !(info.state === 'invite_used' || (info.state === 'open' && info.kind === 'invite' && info.inviteType === 'guest'));
  useEffect(() => {
    if (invalid) api.get('/demo/samples/', { quiet401: true }).then(setSample, () => {});
  }, [invalid]);

  async function submit(e) {
    e.preventDefault();
    setErr('');
    try {
      const res = await api.post('/signup/' + encodeURIComponent(t) + '/', { name: f.name, email: info.email, password: f.password, confirm: f.confirm }, { quiet401: true });
      await app.signedIn(res.user);
      router.push(ROLES[res.user.role].home);
    } catch (x) { setErr(x.message); }
  }

  let body = null;
  if (info) {
    if (invalid) {
      body = (
        <>
          <h1 className="text-2xl font-semibold tracking-tight">This invitation is not valid</h1>
          <p className="mb-6 mt-2 text-sm text-mut">Guest invitations are personal. It may have expired, been cancelled or already been used.</p>
          {sample && sample.guestToken ? <div className="persona-note">Prototype: <Link className="underline" href={'/guest-invite?t=' + sample.guestToken}>open a sample guest invitation</Link></div> : null}
          <Link href="/login" className="mt-5 inline-block text-sm text-mut">Back to sign in</Link>
        </>
      );
    } else if (info.state === 'invite_used') {
      body = (
        <>
          <h1 className="text-2xl font-semibold tracking-tight">Invitation already accepted</h1>
          <p className="mb-6 mt-2 text-sm text-mut">Sign in with your invited email.</p>
          <Link href="/login" className="btn btn-p">Go to sign in</Link>
        </>
      );
    } else {
      const names = (info.companies || []).map((c) => c.name).join(', ');
      body = (
        <>
          <h1 className="text-2xl font-semibold tracking-tight">Accept invitation</h1>
          <p className="mb-6 mt-2 text-sm text-mut">{info.invitedBy || 'A client'} invited you to {names} as a read-only guest. Set your sign-in details to join.</p>
          <form id="f" onSubmit={submit}>
            <label className="lbl" htmlFor="name">Your name</label><input id="name" className="inp mb-3" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} autoComplete="name" required />
            <label className="lbl" htmlFor="email">Invited email</label><input id="email" className="inp mb-3" type="email" value={info.email || ''} readOnly />
            <label className="lbl" htmlFor="password">Create password</label><input id="password" className="inp mb-3" type="password" placeholder="At least 12 characters" autoComplete="new-password" required minLength={12} value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} />
            <label className="lbl" htmlFor="confirm">Confirm password</label><input id="confirm" className="inp" type="password" autoComplete="new-password" required minLength={12} value={f.confirm} onChange={(e) => setF({ ...f, confirm: e.target.value })} />
            <p id="err" className={'mt-3 text-sm' + (err ? '' : ' hidden')} style={{ color: 'var(--bad)' }} role="alert">{err}</p>
            <p className="mt-4 text-xs text-cap">Access includes {names} overview, reports, and trade history.</p>
            <button className="btn btn-p mt-4 w-full">Accept invitation</button>
          </form>
          <Link href="/login" className="mt-5 inline-block text-sm text-mut">Back to sign in</Link>
        </>
      );
    }
  }
  return (
    <>
      <DocTitle title="Accept invitation" />
      <ThemeCorner />
      <div className="guest-page">
        <Link href="/login" className="guest-brand" aria-label="Deltablock home"><svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true"><path d="M16 3 30 29H2z" fill="#F2B705" /><path d="M16 12 21.5 23h-11z" fill="#0A1220" /></svg><span>DELTABLOCK</span></Link>
        <main className="guest-content"><section className="card guest-card" id="gi">{body}</section></main>
      </div>
    </>
  );
}
