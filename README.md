# Deltablock

Deltablock is a web portal prototype for liquidity-service clients and administrators. It brings company-level liquidity metrics, market activity, reports, team access, subscriptions, and support workflows into one role-aware workspace.

> **Prototype notice:** All market and company data in this repository is demonstration data. It is not connected to a live market feed and must not be used for investment or operational decisions. This project is still in progress; review [STATUS.md](./STATUS.md) before relying on feature completeness.

## What the application does

- **Client workspace:** Review liquidity KPIs and trends, market activity, trade history, anonymized peer comparisons, reports, statements, subscriptions, company profiles, team access, and support tickets.
- **Multi-company workspace:** Switch between the companies assigned to an account and view the same company-scoped client features.
- **Guest workspace:** Read-only access to selected overview and market pages.
- **Administration:** Manage companies and users, client sign-up links, access requests, profile-change reviews, subscriptions, feed-health information, access logs, and support tickets.
- **Account access:** Sign in with an email address, request access, register through an invitation or sign-up link, and manage account and password settings.

## Technology and architecture

| Area | Technology | Responsibility |
| --- | --- | --- |
| Frontend | Next.js 15 App Router, React 19, JavaScript | Browser UI, route handling, role-aware navigation, forms, charts, and API calls |
| Backend | Django 5 and Django REST Framework | JSON API, authentication, business rules, company-level authorization, and data access |
| Database | SQLite by default; PostgreSQL supported | Users, company access, market snapshots, subscriptions, support records, and administration data |
| Styling | Tailwind CSS source/configuration and compiled CSS | Responsive layout, theme variables, reusable visual styles |
| API documentation | drf-spectacular / Swagger UI | OpenAPI schema and interactive API reference |

The browser sends API requests to the Next.js origin under `/api/`. Next.js rewrites those requests to Django, keeping session and CSRF cookies same-origin in the normal local setup:

```text
Browser -> Next.js (localhost:3000) -> Django REST API (localhost:8000) -> SQLite/PostgreSQL
```

The API uses Django session authentication. Unsafe requests include the CSRF token in `X-CSRFToken`. The frontend stores only the selected company as a UI preference; the server resolves a user's role and company permissions from database records and enforces them on each request.

## Roles and access

- **Client:** Access to the assigned company's workspace and, when authorized, its team-management tools.
- **Multi-company client:** Client access across multiple assigned companies.
- **Guest:** Read-only access to a limited set of company and market pages.
- **Admin:** Administration pages and company-wide visibility.

Company visibility and manager permissions are stored as company-access records. Frontend route gates improve navigation and user experience, but the Django API is authoritative for authorization and tenant isolation.

## Repository guide

```text
.
|-- backend/
|   |-- accounts/          Custom email-based user model, authentication, and access rules
|   |-- administration/    Sign-up links, access requests, audit records, and access logs
|   |-- common/            Shared API/formatting helpers and the seed_demo command
|   |-- companies/         Companies, company access, and profile-review records
|   |-- config/             Active Django settings, root URLs, ASGI, and WSGI
|   |-- core/               Shared API views, permissions, calculations, CSRF, and helpers
|   |-- deltablock/         Alternate/legacy Django project package; manage.py selects config.settings
|   |-- market/             KPI snapshots, trades, peer groups, reports, feeds, and simulations
|   |-- subscriptions/      Subscription plans, services, and billing statements
|   |-- support/            Support tickets and ticket messages
|   |-- seed/               Demo seed data files
|   |-- seed_assets/        Seed-related assets, including report files
|   |-- manage.py           Django management entry point
|   |-- requirements.txt    Python dependencies
|   `-- db.sqlite3          Default local database (when present)
|-- docs/
|   `-- API_CONTRACT.md     Frontend/backend API contract, shapes, rules, and endpoints
|-- frontend/
|   |-- app/                Next.js routes and page entry points
|   |-- components/         Shared shell, app provider, and UI components
|   |-- features/           Authentication, dashboard, and portal feature UI
|   |-- hooks/              Shared data-loading hooks
|   |-- lib/                API client, formatting, role constants, and calculations
|   |-- public/             Static assets and report PDFs
|   |-- styles/             Tailwind source and configuration
|   |-- tests/              Vitest setup
|   `-- package.json        Frontend scripts and dependencies
|-- tools/
|   `-- parity/             Prototype reference fixtures and calculation-parity tools
`-- STATUS.md               Current project status and known work-in-progress notes
```

### Backend domains

- `accounts` defines the custom email-based user, authentication backend, invitations, account changes, and role/access rules.
- `companies` stores company profiles, per-user company access, and proposed profile changes awaiting review.
- `market` stores sample KPI snapshots, market statistics, peer aggregates, reports, feeds, and trades. `sim.py` provides deterministic sample calculations.
- `subscriptions` stores contracts, contracted services, and statements.
- `support` stores tickets and their message history.
- `administration` stores administration workflows such as access requests and sign-up links, plus audit and access-log records.
- `core` provides shared API views and infrastructure used across domains, including permission checks, calculations, authentication/CSRF helpers, and utility functions.
- `common` contains shared response/formatting helpers and the `seed_demo` management command.

The root API URL configuration is in `backend/config/urls.py`. Domain endpoints are mounted under `/api/`; the Django admin is available under `/admin/`.

### Frontend areas

- `app/` contains the App Router entry points. Authentication has dedicated routes; most signed-in feature routes are rendered through the shared portal page. `/ticket/[ticketId]` handles ticket details.
- `features/auth/` contains sign-in, sign-up, guest invitation, and password-reset interfaces.
- `features/dashboard/` contains the KPI overview.
- `features/portal/` renders the role-aware client and administrator screens.
- `components/AppProvider.jsx` owns shared session and company-selection state. `components/Workspace.jsx` supplies the signed-in navigation shell and page-level UI gates.
- `lib/api.js` is the centralized JSON client, including session credentials and CSRF handling. Other `lib/` modules provide role/navigation constants, formatting, and deterministic display calculations.
- `app/globals.css` contains the compiled application styles; `styles/` contains the Tailwind configuration and source stylesheet.

## API reference and data contract

The API base path is `/api/`. The frontend/backend payload shapes, date formats, error responses, access rules, and endpoint catalog are documented in [docs/API_CONTRACT.md](./docs/API_CONTRACT.md).

When the backend is running, the OpenAPI schema and Swagger UI are available at:

- `http://127.0.0.1:8000/api/schema/`
- `http://127.0.0.1:8000/api/docs/`

In the active Django settings, API documentation is public in debug mode and restricted to administrators otherwise.

## Local development

### Prerequisites

- Python 3.10 or later
- Node.js 20.9 or later and npm

### 1. Install and start the backend

From the repository root, in PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
```

To load the illustrative sample companies, users, subscriptions, reports, and related records, run:

```powershell
python manage.py seed_demo
```

Then start Django:

```powershell
python manage.py runserver 8000
```

The active entry point is `backend/manage.py`, which selects `config.settings`. Local development defaults to debug mode and SQLite at `backend/db.sqlite3`; the default database can be overridden with `DATABASE_URL`. Configure a production-grade `SECRET_KEY`, `ALLOWED_HOSTS`, database URL, and HTTPS settings before deployment. Do not enable demo conveniences or seed sample accounts in production.

To create an administrator interactively, use `python manage.py createsuperuser`.

### 2. Install and start the frontend

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The Next.js rewrite targets `http://127.0.0.1:8000` by default. Override the server-side target with `BACKEND_URL` if Django runs elsewhere. `frontend/.env.example` documents the frontend environment variables; keep `NEXT_PUBLIC_API_BASE_URL=/api` when using the same-origin proxy.

### Database options

SQLite is the default for local development. For PostgreSQL, configure `DATABASE_URL` for the active `config.settings` and provide the PostgreSQL driver from `backend/requirements.txt`. Keep database credentials out of source control.

## Common development commands

### Backend

```powershell
cd backend
python manage.py check
python manage.py test
python manage.py makemigrations
python manage.py migrate
```

### Frontend

```powershell
cd frontend
npm run lint
npm test
npm run build
```

Vitest is configured for the frontend; at the time this README was written, the repository did not contain matching `*.test.*` or `*.spec.*` files, so `npm test` reports that no test files were found.

## Demo data and production considerations

- Seeded market figures, trades, peer groups, and company records are synthetic prototype data. The application does not currently represent a live market-data integration.
- Password reset email uses the console email backend by default. Configure a real email provider before offering account recovery to users.
- `STATUS.md` records that the overall conversion is still in progress. Verify screen coverage, permissions, data sources, operational behavior, and deployment settings before production use.
- Never commit `.env` files, credentials, production database URLs, or real user data.
