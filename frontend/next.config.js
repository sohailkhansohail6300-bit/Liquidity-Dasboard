/** @type {import('next').NextConfig} */
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

/* Original static page names (e.g. dashboard.html) keep working: they redirect to the matching Next.js route. */
const PAGES = [
  'login', 'signup', 'guest-invite', 'password-reset', 'account', 'dashboard', 'market', 'trades', 'comparison',
  'reports', 'accounting', 'subscription', 'company', 'team', 'tickets', 'ticket', 'companies', 'admin',
  'signup-links', 'access-requests', 'profile-reviews', 'users', 'admin-subscriptions', 'data-health',
  'access-log', 'wireframes'
];

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    /* The browser only talks to the Next.js origin; /api/* is proxied to Django so session + CSRF cookies are same-origin. */
    return [{ source: '/api/:path*', destination: `${BACKEND_URL}/api/:path*/` }];
  },
  async redirects() {
    return [
      { source: '/index.html', destination: '/login', permanent: false },
      ...PAGES.map((p) => ({ source: `/${p}.html`, destination: `/${p}`, permanent: false }))
    ];
  },
  /* Django's API URLs end in a slash; do not let Next strip it before proxying. */
  skipTrailingSlashRedirect: true
};

module.exports = nextConfig;
