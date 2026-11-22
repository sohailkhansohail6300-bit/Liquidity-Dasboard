# Deltablock

**A role-aware liquidity operations portal built with Next.js, React, Django REST Framework, and PostgreSQL/SQLite.**

Deltablock is a web application prototype for liquidity-service clients and administrators. It brings company-level liquidity metrics, market activity, trade history, reports, subscriptions, team access, and support workflows into a unified workspace.

> [!IMPORTANT]
> **Prototype / demonstration data only.** Market figures, trades, peer comparisons, and company records currently use synthetic demonstration data. The application is not connected to a live market-data feed and must not be used for investment, financial, or operational decisions. The project is still under active development and is not represented as production-ready.

---

## Contents

- [Overview](#overview)
- [Core capabilities](#core-capabilities)
- [Technology stack](#technology-stack)
- [Architecture](#architecture)
- [Roles and authorization](#roles-and-authorization)
- [Repository structure](#repository-structure)
- [Backend domains](#backend-domains)
- [Frontend structure](#frontend-structure)
- [API documentation](#api-documentation)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Development commands](#development-commands)
- [Demo data](#demo-data)
- [Security and production readiness](#security-and-production-readiness)
- [Project status](#project-status)

## Overview

Deltablock is organized around a clear separation of responsibilities:

- **Next.js frontend** — renders the user experience, handles navigation and forms, and communicates with the API.
- **Django REST backend** — owns authentication, business rules, data access, and authorization.
- **Relational database** — stores users, company access, market snapshots, subscriptions, support records, and administrative workflows.

The frontend uses a same-origin `/api/` route and a Next.js rewrite to proxy requests to Django during local development. This keeps session and CSRF cookies on the frontend origin in the standard local setup.

## Core capabilities

### Client workspace

- Liquidity KPIs, trends, and market activity
- Trade history and anonymized peer comparisons
- Reports and statements
- Subscription and contracted-service information
- Company profile and team-access workflows
- Support tickets and ticket conversations

### Multi-company workspace

Users assigned to more than one company can switch between their authorized company workspaces. Company-scoped data is resolved and authorized by the backend.

### Guest workspace

Provides read-only access to selected overview and market pages.

### Administration

Administrative workflows include:

- Company and user management
- Client sign-up links and access requests
- Profile-change review
- Subscription administration
- Feed-health information
- Access logs and audit records
- Support-ticket management

### Account access

- Email-based sign-in
- Access requests
- Invitation and sign-up-link registration
- Account and password settings

## Technology stack

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | Next.js 15 App Router, React 19, JavaScript | UI, routing, navigation, forms, charts, and API integration |
| Backend | Django 5, Django REST Framework | JSON API, authentication, business logic, permissions, and data access |
| Database | SQLite (default), PostgreSQL (supported) | Application and business records |
| Styling | Tailwind CSS source/configuration and compiled CSS | Responsive layout, theme variables, and reusable styling |
| API documentation | drf-spectacular, Swagger UI | OpenAPI schema and interactive API reference |
| Frontend testing | Vitest | Frontend test runner and test configuration |

## Architecture

```text
┌──────────────────────────────┐
│       Browser / Client       │
└──────────────┬───────────────┘
               │ Same-origin /api/ requests
               ▼
┌──────────────────────────────┐
│     Next.js (localhost:3000) │
│       App Router + UI        │
└──────────────┬───────────────┘
               │ Next.js rewrite
               ▼
┌──────────────────────────────┐
│   Django REST API (:8000)    │
│ Auth • Permissions • Rules   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       SQLite / PostgreSQL    │
└──────────────────────────────┘
```

### Authentication and request security

The API uses Django session authentication. Unsafe requests send the CSRF token through the `X-CSRFToken` header.

The frontend may retain the selected company as a UI preference, but it does not establish authorization. The backend resolves the user's role and company permissions from database records and enforces access on each request.

## Roles and authorization

| Role | Access |
|---|---|
| Client | Assigned company workspace and authorized team-management features |
| Multi-company client | Client features across multiple assigned companies |
| Guest | Read-only access to selected company and market pages |
| Admin | Administrative screens and company-wide visibility |

Company visibility and manager permissions are represented by company-access records. Frontend route gates support navigation and user experience; **the Django API is the authoritative security boundary** for authorization and tenant isolation.

## Repository structure

```text
.
├── backend/
│   ├── accounts/          # Custom email user, authentication, and access rules
│   ├── administration/    # Sign-up links, access requests, audit records, access logs
│   ├── common/            # Shared helpers and seed_demo management command
│   ├── companies/         # Companies, company access, profile-review records
│   ├── config/            # Active Django settings, root URLs, ASGI, and WSGI
│   ├── core/              # Shared API views, permissions, calculations, and helpers
│   ├── deltablock/        # Alternate/legacy project package
│   ├── market/            # KPI snapshots, trades, peer groups, reports, feeds, simulations
│   ├── subscriptions/     # Plans, contracted services, and billing statements
│   ├── support/           # Support tickets and ticket messages
│   ├── seed/              # Demonstration seed data
│   ├── seed_assets/       # Seed-related assets, including report files
│   ├── manage.py          # Django management entry point
│   └── requirements.txt   # Python dependencies
├── docs/
│   └── API_CONTRACT.md    # API payloads, rules, and endpoint contract
├── frontend/
│   ├── app/               # Next.js App Router pages and route entry points
│   ├── components/        # Shared application shell and UI components
│   ├── features/          # Authentication, dashboard, and portal features
│   ├── hooks/             # Shared data-loading hooks
│   ├── lib/               # API client, formatting, roles, and calculations
│   ├── public/            # Static assets and report PDFs
│   ├── styles/            # Tailwind source and configuration
│   ├── tests/             # Vitest configuration and test support
│   └── package.json       # Frontend scripts and dependencies
├── tools/
│   └── parity/            # Prototype fixtures and calculation-parity tools
└── STATUS.md              # Current project status and known work in progress
```

The active Django entry point is `backend/manage.py`, which selects `config.settings`. The alternate `backend/deltablock/` package is retained as a legacy/alternate project package.

## Backend domains

| Django app | Responsibility |
|---|---|
| `accounts` | Custom email-based user model, authentication, invitations, account changes, and role/access rules |
| `companies` | Company profiles, per-user company access, and profile changes awaiting review |
| `market` | Sample KPI snapshots, market statistics, peer aggregates, reports, feeds, and trades |
| `subscriptions` | Subscription contracts, contracted services, and statements |
| `support` | Support tickets and message history |
| `administration` | Access requests, sign-up links, audit records, and access logs |
| `core` | Shared API views, permissions, calculations, authentication/CSRF helpers, and utilities |
| `common` | Shared response/formatting helpers and the `seed_demo` command |

The root API URL configuration is `backend/config/urls.py`. Domain endpoints are mounted under `/api/`; Django Admin is available under `/admin/`.

## Frontend structure

- `app/` contains the Next.js App Router entry points. Authentication has dedicated routes; most signed-in feature routes use the shared portal page. `/ticket/[ticketId]` renders ticket details.
- `features/auth/` contains sign-in, sign-up, guest invitation, and password-reset interfaces.
- `features/dashboard/` contains the KPI overview.
- `features/portal/` renders role-aware client and administrator screens.
- `components/AppProvider.jsx` manages shared session and company-selection state.
- `components/Workspace.jsx` provides the signed-in navigation shell and page-level UI gates.
- `lib/api.js` centralizes JSON requests, session credentials, and CSRF handling.
- `app/globals.css` contains compiled application styles; `styles/` contains Tailwind configuration and source stylesheets.

## API documentation

The API base path is:

```text
/api/
```

The frontend/backend payload shapes, date formats, error responses, access rules, and endpoint catalog are documented in [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md).

When the Django backend is running, the OpenAPI schema and Swagger UI are available at:

- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- Swagger UI: `http://127.0.0.1:8000/api/docs/`

In the active Django settings, API documentation is public in debug mode and restricted to administrators otherwise.

## Getting started

### Prerequisites

Install the following before starting the project:

- Python 3.10 or later
- Node.js 20.9 or later
- npm

### 1. Set up the backend

From the repository root, open a terminal and run:

```powershell
cd backend

# Create and activate a virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
python -m pip install -r requirements.txt

# Apply database migrations
python manage.py migrate
```

To load the illustrative companies, users, subscriptions, reports, and related records:

```powershell
python manage.py seed_demo
```

Create an administrator account interactively when needed:

```powershell
python manage.py createsuperuser
```

Start the Django development server:

```powershell
python manage.py runserver 8000
```

The backend will be available at `http://127.0.0.1:8000/`.

### 2. Set up the frontend

Open a second terminal from the repository root:

```powershell
cd frontend

# Install dependencies from the lockfile
npm ci

# Start the Next.js development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000/) in your browser.

By default, the Next.js rewrite sends API requests to `http://127.0.0.1:8000`. Set `BACKEND_URL` if Django runs at a different address. See `frontend/.env.example` for the frontend environment variables. When using the same-origin proxy, keep `NEXT_PUBLIC_API_BASE_URL=/api`.

## Configuration

### Database

SQLite is used by default for local development. PostgreSQL is also supported. Configure `DATABASE_URL` for the active `config.settings` and ensure the PostgreSQL driver listed in `backend/requirements.txt` is installed.

Keep database credentials outside source control.

### Backend and frontend environment

- Configure a secure, environment-specific Django `SECRET_KEY`.
- Set `ALLOWED_HOSTS` for the domains serving the backend.
- Configure `DATABASE_URL` when using a database other than the local SQLite default.
- Configure `BACKEND_URL` when the Django API is not running at `http://127.0.0.1:8000`.
- Use `NEXT_PUBLIC_API_BASE_URL=/api` with the same-origin Next.js proxy.
- Use `frontend/.env.example` as the reference for frontend environment variables.

Do not commit real `.env` files or secrets.

## Development commands

Run backend commands from `backend/`:

```powershell
# Validate Django configuration
python manage.py check

# Run backend tests
python manage.py test

# Create migration files after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

Run frontend commands from `frontend/`:

```powershell
# Lint the frontend
npm run lint

# Run frontend tests
npm test

# Create a production build
npm run build
```

**Testing note:** Vitest is configured for the frontend. At the time this README was prepared, the repository did not contain matching `*.test.*` or `*.spec.*` files, so `npm test` reports that no test files were found.

## Demo data

The `seed_demo` management command creates illustrative sample records. Seeded market figures, trades, peer groups, and company records are synthetic. The application does not currently include a live market-data integration.

Do not use seeded accounts or sample records as real customer, financial, or operational data.

## Security and production readiness

Before any production deployment, review and verify at minimum:

- Replace development secrets with securely managed production secrets.
- Configure production `ALLOWED_HOSTS`, HTTPS, secure cookies, and CSRF trusted origins as appropriate for the deployment.
- Configure a production database and protect its credentials.
- Configure a real email provider; password-reset email uses Django's console email backend by default.
- Review authentication, permissions, company-level access, and tenant-isolation behavior.
- Verify all data sources and replace demonstration data with validated production integrations.
- Disable development-only conveniences and do not seed sample accounts in production.
- Review file handling, logging, backups, monitoring, and deployment configuration.
- Run backend checks, tests, frontend linting, and a production frontend build.
- Confirm the outstanding work recorded in `STATUS.md`.

This checklist is not a claim that these production controls are already implemented. The project must be independently reviewed and tested before handling real users or business data.

## Project status

Deltablock is a work in progress. `STATUS.md` is the source of truth for current implementation status and known gaps. Screen coverage, authorization, data sources, operational behavior, and deployment settings still require verification before production use.

---

## License

No license information was specified in the supplied project README. Add a `LICENSE` file and update this section before distributing the project as open source.
