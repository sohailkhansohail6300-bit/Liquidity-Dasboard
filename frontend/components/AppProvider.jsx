'use client';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { api, onUnauthorized } from '@/lib/api';

const Ctx = createContext(null);
export function useApp() { return useContext(Ctx); }

const PUBLIC = ['/login', '/signup', '/guest-invite', '/password-reset'];

/* Session, visible companies, selected company and toast for the whole app. All business data comes from the Django API;
   only the *selected company id* (a UI preference) is remembered in localStorage and is always re-validated against the API's visible list. */
export default function AppProvider({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [meta, setMeta] = useState({ today: '2026-10-23', demoMode: false });
  const [selected, setSelected] = useState(null);
  const [counts, setCounts] = useState({ accessRequestsPending: 0, profileReviewsPending: 0 });
  const [toastState, setToastState] = useState({ msg: '', kind: 'ok', show: false });
  const timer = useRef(null);

  const loadCompanies = useCallback(async () => {
    const list = await api.get('/companies/');
    setCompanies(list);
    return list;
  }, []);
  const loadCounts = useCallback(async (user) => {
    if (user && user.role === 'admin') {
      try { setCounts(await api.get('/admin/counts/')); } catch (e) { /* non-critical */ }
    }
  }, []);

  const bootstrap = useCallback(async () => {
    try { setMeta(await api.get('/meta/', { quiet401: true })); } catch (e) { /* defaults */ }
    try {
      const r = await api.get('/auth/me/', { quiet401: true });
      if (r.user) { setMe(r.user); await loadCompanies(); await loadCounts(r.user); } else { setMe(null); setCompanies([]); }
    } catch (e) { setMe(null); setCompanies([]); }
    try { setSelected(JSON.parse(localStorage.getItem('dbt-company'))); } catch (e) { /* ignore */ }
    setLoading(false);
  }, [loadCompanies, loadCounts]);

  useEffect(() => { bootstrap(); }, [bootstrap]);

  useEffect(() => {
    onUnauthorized(() => { setMe(null); setCompanies([]); if (PUBLIC.indexOf(window.location.pathname) < 0) router.replace('/login'); });
  }, [router]);

  const toast = useCallback((msg, kind) => {
    setToastState({ msg, kind: kind === 'err' ? 'err' : 'ok', show: true });
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setToastState((s) => ({ ...s, show: false })), kind === 'err' ? 6000 : 3600);
  }, []);

  const companyMap = useMemo(() => { const m = {}; companies.forEach((c) => { m[c.id] = c; }); return m; }, [companies]);
  const allowed = useMemo(() => companies.map((c) => c.id), [companies]);
  const co = (selected && companyMap[selected]) || companies[0] || null;

  const setCompany = useCallback((id) => {
    if (!companyMap[id]) return false;
    setSelected(id);
    try { localStorage.setItem('dbt-company', JSON.stringify(id)); } catch (e) { /* ignore */ }
    return true;
  }, [companyMap]);

  /* Called after sign-in / registration / account changes with the Me object returned by the API. */
  const signedIn = useCallback(async (user) => {
    setMe(user);
    setSelected(null);
    try { localStorage.removeItem('dbt-company'); } catch (e) { /* ignore */ }
    await loadCompanies();
    await loadCounts(user);
  }, [loadCompanies, loadCounts]);

  const refreshMe = useCallback(async () => {
    const r = await api.get('/auth/me/', { quiet401: true });
    setMe(r.user);
    if (r.user) await loadCompanies();
    return r.user;
  }, [loadCompanies]);

  const signOut = useCallback(async () => {
    try { await api.post('/auth/logout/', {}, { quiet401: true }); } catch (e) { /* session may already be gone */ }
    setMe(null); setCompanies([]); setSelected(null);
    try { localStorage.removeItem('dbt-company'); } catch (e) { /* ignore */ }
  }, []);

  const can = useMemo(() => ({
    manage: (id) => !!me && me.role !== 'guest' && !!id && me.manages.indexOf(id) >= 0,
    editProfile: (id) => !!me && me.role !== 'admin' && me.role !== 'guest' && !!id && me.manages.indexOf(id) >= 0
  }), [me]);

  const value = useMemo(() => ({
    loading, me, companies, companyMap, allowed, co, meta, counts, pathname,
    setCompany, signedIn, refreshMe, refreshCompanies: loadCompanies, refreshCounts: () => loadCounts(me), signOut, toast, can
  }), [loading, me, companies, companyMap, allowed, co, meta, counts, pathname, setCompany, signedIn, refreshMe, loadCompanies, loadCounts, signOut, toast, can]);

  return (
    <Ctx.Provider value={value}>
      {children}
      <div id="toast" className={'toast' + (toastState.show ? ' show' : '')} role="status" aria-live="polite">
        {toastState.msg ? (<><span className={'bd ' + (toastState.kind === 'err' ? 'bad' : 'ok')}>{toastState.kind === 'err' ? 'Check' : 'Done'}</span>{toastState.msg}</>) : null}
      </div>
    </Ctx.Provider>
  );
}
