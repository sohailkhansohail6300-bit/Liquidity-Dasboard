/* Centralised API client. Every request goes to the Django REST API (see docs/API_CONTRACT.md).
   Session cookie + CSRF: the CSRF token lives in a cookie set by GET /auth/csrf/ and is echoed in X-CSRFToken. */
const BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || '/api').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(status, data) {
    super((data && data.error) || (data && data.detail) || 'Request failed (' + status + ').');
    this.status = status;
    this.data = data || {};
    this.errors = (data && data.errors) || null;
    this.code = data && data.code;
    this.field = data && data.field;
  }
}

let unauthorizedHandler = null;
export function onUnauthorized(fn) { unauthorizedHandler = fn; }

function cookie(name) {
  if (typeof document === 'undefined') return '';
  const m = document.cookie.split('; ').find((c) => c.startsWith(name + '='));
  return m ? decodeURIComponent(m.slice(name.length + 1)) : '';
}

async function csrfToken() {
  let t = cookie('csrftoken');
  if (!t) {
    try { await fetch(BASE + '/auth/csrf/', { credentials: 'include' }); } catch (e) { /* surfaced by the real request */ }
    t = cookie('csrftoken');
  }
  return t;
}

async function request(method, path, body, opts) {
  const headers = { Accept: 'application/json' };
  const init = { method, credentials: 'include', headers };
  if (body !== undefined) { headers['Content-Type'] = 'application/json'; init.body = JSON.stringify(body); }
  if (!/^(GET|HEAD|OPTIONS)$/.test(method)) {
    const t = await csrfToken();
    if (t) headers['X-CSRFToken'] = t;
  }
  let res;
  try { res = await fetch(BASE + path, init); }
  catch (e) { throw new ApiError(0, { error: 'Could not reach the server. Check your connection and try again.' }); }
  if (res.status === 204) return null;
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  if (!res.ok) {
    if (res.status === 401 && !(opts && opts.quiet401) && unauthorizedHandler) unauthorizedHandler();
    throw new ApiError(res.status, data);
  }
  return data;
}

export const api = {
  get: (p, o) => request('GET', p, undefined, o),
  post: (p, b, o) => request('POST', p, b === undefined ? {} : b, o),
  put: (p, b, o) => request('PUT', p, b, o),
  patch: (p, b, o) => request('PATCH', p, b, o),
  del: (p, o) => request('DELETE', p, undefined, o)
};

export function qstr(params) {
  const u = new URLSearchParams();
  Object.keys(params || {}).forEach((k) => { if (params[k] !== undefined && params[k] !== null && params[k] !== '') u.set(k, params[k]); });
  const s = u.toString();
  return s ? '?' + s : '';
}
