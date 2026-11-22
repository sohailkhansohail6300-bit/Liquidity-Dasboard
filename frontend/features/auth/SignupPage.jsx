'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useApp } from '@/components/AppProvider';
import { AuthShell, DocTitle } from '@/components/ui';
import { useQueryParams } from '@/hooks/useLoad';
import { ROLES } from '@/lib/roles';
import { fmtDate } from '@/lib/format';

function Msg({ title, text, extra }) {
  return (
    <>
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="mb-6 mt-2 text-sm text-mut">{text}</p>
      {extra}
      <Link href="/login" className="mt-5 inline-block text-sm text-mut underline">Back to sign in</Link>
    </>
  );
}

export default function SignupPage() {
  const app = useApp();
  const router = useRouter();
  const q = useQueryParams();
  const t = q ? q.get('t') : undefined;
  const [info, setInfo] = useState(undefined);
  const [sample, setSample] = useState(null);
  const [f, setF] = useState({ nm: '', em: '', pw: '', pw2: '' });
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (q === null) return;
    if (!t) { setInfo({ state: 'invalid' }); return; }
    api.get('/signup/' + encodeURIComponent(t) + '/', { quiet401: true }).then((r) => {
      setInfo(r);
      if (r.state === 'open' && r.kind === 'invite') setF((x) => ({ ...x, nm: r.name || '', em: r.email || '' }));
    }, () => setInfo({ state: 'invalid' }));
  }, [q, t]);

  useEffect(() => {
    if (info && info.state === 'invalid') api.get('/demo/samples/', { quiet401: true }).then(setSample, () => {});
  }, [info]);

  useEffect(() => {
    if (info && info.state === 'open' && info.kind === 'invite' && info.inviteType === 'guest') router.replace('/guest-invite?t=' + encodeURIComponent(t));
  }, [info, t, router]);

  async function submit(e) {
    e.preventDefault();
    setErr(null);
    try {
      const res = await api.post('/signup/' + encodeURIComponent(t) + '/', { name: f.nm, email: f.em, password: f.pw, confirm: f.pw2 }, { quiet401: true });
      await app.signedIn(res.user);
      router.push(ROLES[res.user.role].home);
    } catch (x) {
      const code = x.code;
      if (code === 'duplicate') { setErr({ dup: true, text: x.message }); return; }
      if (code === 'used' || code === 'expired' || code === 'invalid') { window.location.reload(); return; }
      setErr({ text: x.message });
    }
  }

  let body = null;
  if (info) {
    if (info.state === 'invalid') {
      body = (
        <Msg title="This sign-up link is not valid" text="Sign-up links are sent by Deltablock. Check that you opened the full link, or ask us for a new one."
          extra={(<>{sample && sample.signupToken ? <div className="persona-note">Prototype: <Link className="underline" href={'/signup?t=' + sample.signupToken}>open a sample client sign-up link</Link></div> : null}<p className="mt-4 text-sm text-mut">Not a client yet? <Link className="underline" href="/login#request">Request access</Link>.</p></>)} />
      );
    } else if (info.state === 'used') {
      body = <Msg title="This link was already used" text={'An account was created with this link on ' + (info.usedOnIso ? fmtDate(info.usedOnIso) : 'an earlier date') + '. Sign in instead, or ask Deltablock if you need access to another company.'} extra={<Link className="btn btn-p w-full" href="/login">Go to sign in</Link>} />;
    } else if (info.state === 'expired') {
      body = <Msg title="This link has expired" text="Sign-up links are valid for a limited time or may have been revoked. Ask Deltablock to send you a new one." extra={<a className="btn btn-p w-full" href="mailto:support@deltablock.example?subject=New%20sign-up%20link">Ask for a new link</a>} />;
    } else if (info.state === 'no_companies') {
      body = <Msg title="This link cannot be used" text="The companies for this link no longer exist. Ask Deltablock for a new link." />;
    } else if (info.state === 'invite_used') {
      body = <Msg title="This invitation was already used" text="Sign in with your invited email." extra={<Link className="btn btn-p w-full" href="/login">Go to sign in</Link>} />;
    } else if (info.state === 'open' && info.kind === 'invite' && info.inviteType === 'guest') {
      body = null;
    } else if (info.state === 'open') {
      const link = info.kind === 'link';
      const cos = info.companies || [];
      const intro = link
        ? 'You have been given access to the companies below. Enter your own details to create your account.'
        : info.inviteType === 'admin'
          ? (info.invitedBy || 'An administrator') + ' added you as a Deltablock administrator. Choose your name and password to finish setting up your account.'
          : (info.invitedBy || 'A colleague') + ' invited you to join their team as a colleague. Choose your name and password to get started.';
      body = (
        <>
          <h1 className="text-2xl font-semibold tracking-tight">Create your account</h1>
          <p className="mb-6 mt-1 text-sm text-mut">{intro}</p>
          <form id="f" className="space-y-4" noValidate onSubmit={submit}>
            <div><label className="lbl" htmlFor="nm">Your name</label><input id="nm" className="inp" value={f.nm} onChange={(e) => setF({ ...f, nm: e.target.value })} autoComplete="name" required /></div>
            {link
              ? <div><label className="lbl" htmlFor="em">Email</label><input id="em" className="inp" type="email" autoComplete="email" required aria-describedby="err" value={f.em} onChange={(e) => setF({ ...f, em: e.target.value })} /></div>
              : <div><label className="lbl" htmlFor="em">Email</label><input id="em" className="inp" type="email" value={info.email || ''} readOnly /></div>}
            {cos.length ? (
              <div><div className="lbl">Company access <span className="font-normal text-cap">(set by Deltablock, cannot be changed)</span></div><div className="space-y-2">
                {cos.map((c) => (<div className="check-row !cursor-default" key={c.id}><span className="grid h-5 w-5 place-items-center rounded-full bg-[var(--okb)] text-[var(--ok)]" aria-hidden="true">&#10003;</span><b>{c.name}</b><span className="ml-auto text-xs text-cap">{c.exch}</span></div>))}
              </div></div>
            ) : <div className="persona-note">Administrator account: access to every company and the admin pages.</div>}
            <div><label className="lbl" htmlFor="pw">Password</label><input id="pw" type="password" className="inp" placeholder="At least 12 characters" autoComplete="new-password" required value={f.pw} onChange={(e) => setF({ ...f, pw: e.target.value })} /></div>
            <div><label className="lbl" htmlFor="pw2">Confirm password</label><input id="pw2" type="password" className="inp" autoComplete="new-password" required value={f.pw2} onChange={(e) => setF({ ...f, pw2: e.target.value })} /></div>
            <div id="err" className={'text-sm' + (err ? '' : ' hidden')} style={{ color: 'var(--bad)' }} role="alert">
              {err && err.dup ? (
                <div className="card p-4"><p className="font-medium text-ink">{err.text}</p><p className="mt-2 text-mut">An administrator can give you access to another company under Users &rarr; Edit access. This link has not been used up.</p><Link className="btn btn-p mt-3" href="/login">Log in</Link></div>
              ) : (err ? err.text : null)}
            </div>
            <button className="btn btn-p w-full !py-2.5">Create account</button>
            <p className="text-xs text-cap">Prototype: the account is saved in this browser only and the password is neither stored nor checked.</p>
          </form>
          <Link href="/login" className="mt-5 inline-block text-sm text-mut">Back to sign in</Link>
        </>
      );
    }
  }
  return (<><DocTitle title="Create account" /><AuthShell>{body}</AuthShell></>);
}
