import { NextResponse } from 'next/server';

/* First line of defence for protected routes: no Django session cookie => go to /login.
   (The cookie's presence is not trusted for anything else; the API validates the session on every request.) */
const PUBLIC = ['/login', '/signup', '/guest-invite', '/password-reset'];

export function middleware(req) {
  const { pathname } = req.nextUrl;
  if (PUBLIC.includes(pathname) || pathname === '/') return NextResponse.next();
  if (!req.cookies.get(process.env.SESSION_COOKIE_NAME || 'sessionid')) {
    const url = req.nextUrl.clone();
    url.pathname = '/login';
    url.search = '';
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = { matcher: ['/((?!api/|_next/|reports/|favicon.ico|.*\\..*).*)'] };
