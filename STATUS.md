# Project Status

**Overall:** Deltablock is a working prototype and remains under development. It is not production-ready.

## Current implementation

- **Frontend:** Next.js and React application with authentication pages, a client dashboard, and role-aware client/admin portal screens.
- **Backend:** Django REST API with account, company, market, subscription, support, and administration areas.
- **Data:** SQLite is configured for local development; PostgreSQL is supported. Included market and company data is synthetic demonstration data, not a live feed.
- **Access:** The API uses session authentication and CSRF protection, with role and company permissions enforced on the server.
- **Email:** Password-reset email uses the console backend by default; configure a real provider before deployment.

## Validation

The latest recorded local checks completed with:

- `python manage.py check` — passed.
- `python manage.py test` — 4 backend tests passed.
- `npm run lint` — passed.
- `npm test` — no frontend test files were found.

## Remaining work

- Add frontend and end-to-end tests for key user workflows and role permissions.
- Verify feature completeness and cross-browser behavior.
- Connect and validate production data sources and email delivery.
- Review deployment configuration, security controls, and operational monitoring before production use.
