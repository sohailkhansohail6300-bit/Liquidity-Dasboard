'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useApp } from '@/components/AppProvider';
import { AuthShell, DocTitle, Modal } from '@/components/ui';
import { ROLES } from '@/lib/roles';

const MENU = {
  client: 'Overview, Market activity, Trade history, Peer comparison, Reports, Statements, Subscription, Company profile, Team, Support',
  multi: 'Companies plus the full client menu',
  guest: 'Overview, Market activity, Trade history, Peer comparison, Reports, Company profile (read-only)',
  admin: 'Admin overview, Companies, Sign-up links, Access requests, Profile reviews, Users, Subscriptions, Data health, Access log, Support tickets, Screen map'
};

export default function LoginPage() {
  const app = useApp();
  const router = useRouter();
  const [role, setRole] = useState('client');
  const [email, setEmail] = useState(ROLES.client.email);
  const [pass, setPass] = useState('prototype-password');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  const [done, setDone] = useState(false);
  const [rq, setRq] = useState({ name: '', email: '', company: '', msg: '' });

  useEffect(() => { if (window.location.hash === '#request') setOpen(true); }, []);

  function openRequest(e) {
    e.preventDefault();
    setRq({ name: '', email: '', company: '', msg: '' });
    setDone(false);
    setOpen(true);
  }

  async function submit(e) {
    e.preventDefault();
    setErr('');
    setBusy(true);
    try {
      const res = await api.post('/auth/login/', { email: email.trim(), password: pass }, { quiet401: true });
      await app.signedIn(res.user);
      router.push(ROLES[res.user.role].home);
    } catch (x) {
      setErr(x.message);
      setBusy(false);
    }
  }

  async function sendRequest(e) {
    e.preventDefault();
    try {
      await api.post('/access-requests/', { name: rq.name.trim(), email: rq.email.trim(), company: rq.company.trim(), message: rq.msg.trim() }, { quiet401: true });
      setDone(true);
    } catch (x) {
      app.toast(x.message, 'err');
    }
  }

  const r = ROLES[role];
  return (
    <>
      <DocTitle title="Login" />
      <AuthShell>
        <h1 className="text-2xl font-semibold tracking-tight">Welcome back</h1>
        <p className="mb-6 mt-1 text-sm text-mut">Sign in to access your workspace.</p>
        <form id="login" className="space-y-4" onSubmit={submit}>
          <div className="persona-note">
            <label className="lbl !mb-1" htmlFor="role">Prototype: sign in as</label>
            <select id="role" className="inp" value={role} onChange={(e) => { setRole(e.target.value); setEmail(ROLES[e.target.value].email); }}>
              <option value="client">Client (one company)</option>
              <option value="multi">Multi-company client</option>
              <option value="guest">Guest (read-only)</option>
              <option value="admin">Admin</option>
            </select>
            <p id="role-hint" className="mt-2" aria-live="polite">Lands on <b className="text-ink">{r.homeName}</b>. Menu: {MENU[role]}.</p>
          </div>
          <div><label className="lbl" htmlFor="email">Work email</label><input id="email" name="email" type="email" className="inp" placeholder="name@company.com" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} /></div>
          <div><label className="lbl" htmlFor="pass">Password</label><input id="pass" name="pass" type="password" className="inp" placeholder="Enter your password" required value={pass} onChange={(e) => setPass(e.target.value)} /></div>
          <div className="flex justify-between text-sm"><label className="flex items-center gap-2 text-mut"><input type="checkbox" className="text-sm font-small accent-[#F2B705]" /> Remember me</label><Link href="/password-reset" className="text-sm sm:font-small underline">Forgot password?</Link></div>
          <p id="login-err" className="field-err" role="alert" hidden={!err}>{err}</p>
          <button className="btn btn-p w-full !py-2.5" disabled={busy}>Login</button>
          <p className="text-xs text-cap">Prototype: the password is not checked. Pick a persona above, or type the email of an account created through a sign-up link, invitation or Add admin.</p>
        </form>
        <div className="mt-6 border-t pt-5 text-center text-sm text-mut">Not a client yet? <a className="font-semibold text-ink underline" href="#request" onClick={openRequest}>Request access</a><p className="mt-1 text-xs text-cap">Existing clients join through the sign-up link we email them.</p></div>
      </AuthShell>
      <Modal id="request-modal" open={open} onClose={() => setOpen(false)} labelledBy="rt">
        <div className="card w-full max-w-md">
          <div id="req-form-wrap" className={done ? 'hidden' : undefined}>
            <div className="border-b px-6 py-4"><h2 id="rt" className="font-semibold">Request access</h2><p className="text-sm text-cap">Tell us who you are. We review every request and send approved people a sign-up link.</p></div>
            <form id="req" className="space-y-4 p-6" onSubmit={sendRequest}>
              <div><label className="lbl" htmlFor="rq-name">Name</label><input id="rq-name" className="inp" required autoComplete="name" value={rq.name} onChange={(e) => setRq({ ...rq, name: e.target.value })} /></div>
              <div><label className="lbl" htmlFor="rq-email">Email</label><input id="rq-email" type="email" className="inp" required autoComplete="email" value={rq.email} onChange={(e) => setRq({ ...rq, email: e.target.value })} /></div>
              <div><label className="lbl" htmlFor="rq-company">Company</label><input id="rq-company" className="inp" required autoComplete="organization" value={rq.company} onChange={(e) => setRq({ ...rq, company: e.target.value })} /></div>
              <div><label className="lbl" htmlFor="rq-msg">Message</label><textarea id="rq-msg" className="inp h-24" placeholder="What would you like to see in Deltablock?" value={rq.msg} onChange={(e) => setRq({ ...rq, msg: e.target.value })} /></div>
              <div className="flex justify-end gap-2"><button type="button" className="btn" onClick={() => setOpen(false)}>Cancel</button><button className="btn btn-p">Send request</button></div>
            </form>
          </div>
          <div id="req-done" className={(done ? '' : 'hidden ') + 'p-8 text-center'}>
            <h2 className="text-lg font-semibold">Request sent</h2>
            <p className="mb-6 mt-2 text-sm text-mut">Thank you. We will review it and email you a sign-up link if it is approved.</p>
            <button type="button" className="btn btn-p" onClick={() => setOpen(false)}>Back to sign in</button>
          </div>
        </div>
      </Modal>
    </>
  );
}
