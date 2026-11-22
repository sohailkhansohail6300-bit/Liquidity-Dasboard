'use client';
import { useCallback, useEffect, useRef, useState } from 'react';

/* Small data-loading hook: runs `fn()` (an api call) whenever `deps` change; `reload()` runs it again.
   State: { data, error (ApiError|null), loading }. A stale response never overwrites a newer one. */
export function useLoad(fn, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [tick, setTick] = useState(0);
  const fnRef = useRef(fn);
  fnRef.current = fn;
  useEffect(() => {
    let live = true;
    setState((s) => ({ data: s.data, error: null, loading: true }));
    Promise.resolve()
      .then(() => fnRef.current())
      .then(
        (data) => { if (live) setState({ data, error: null, loading: false }); },
        (error) => { if (live) setState({ data: null, error, loading: false }); }
      );
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...(deps || []), tick]);
  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { ...state, reload };
}

/* Reads window.location.search after mount (null on the server and on the first client render, so there is no hydration mismatch). */
export function useQueryParams() {
  const [q, setQ] = useState(null);
  useEffect(() => { setQ(new URLSearchParams(window.location.search)); }, []);
  return q;
}

/* localStorage-backed UI preference (theme, selected period...). Never used for business data or credentials. */
export function useLocalPref(key, initial, allowed) {
  const [v, setV] = useState(initial);
  useEffect(() => {
    try {
      const s = localStorage.getItem('dbt-' + key);
      if (s !== null) { const parsed = JSON.parse(s); if (!allowed || allowed.indexOf(parsed) >= 0) setV(parsed); }
    } catch (e) { /* storage unavailable: keep default */ }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  const set = useCallback((x) => { setV(x); try { localStorage.setItem('dbt-' + key, JSON.stringify(x)); } catch (e) { /* ignore */ } }, [key]);
  return [v, set];
}
