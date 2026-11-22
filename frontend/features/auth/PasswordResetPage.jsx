'use client';
import { useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { DocTitle, ThemeCorner } from '@/components/ui';

export default function PasswordResetPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  async function submit(e) {
    e.preventDefault();
    /* The confirmation is the same whether or not an account exists (no account enumeration). */
    try { await api.post('/auth/password/reset/', { email: email.trim() }, { quiet401: true }); } catch (x) { /* shown message does not depend on the outcome */ }
    setSent(true);
  }
  return (
    <>
      <DocTitle title="Reset password" />
      <ThemeCorner />
      <div className="grid min-h-screen place-items-center p-5">
        <section className="card w-full max-w-md p-8">
          <Link href="/login" className="inline-flex items-center gap-2.5 text-sm font-semibold tracking-[.14em]"><svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true"><path d="M16 3 30 29H2z" fill="#F2B705" /><path d="M16 12 21.5 23h-11z" fill="#0A1220" /></svg>DELTABLOCK</Link>
          <h1 className="page-title mt-8">Reset password</h1>
          <p className="mb-6 mt-3 text-sm text-mut">Enter your account email. We will send a secure link to choose a new password.</p>
          <form id="rf" onSubmit={submit}><label className="lbl" htmlFor="email">Work email</label><input id="email" type="email" className="inp" placeholder="name@company.com" required value={email} onChange={(e) => setEmail(e.target.value)} /><button className="btn btn-p mt-4 w-full">Send reset link</button></form>
          <p id="sent" className={'mt-4 rounded-md bg-hov p-3 text-sm text-mut' + (sent ? '' : ' hidden')} role="status">If an account exists for this address, a reset link has been sent.</p>
          <Link href="/login" className="mt-5 inline-block text-sm text-mut">Back to sign in</Link>
        </section>
      </div>
    </>
  );
}
