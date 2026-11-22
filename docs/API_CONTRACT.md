# Deltablock API Contract

This document describes the REST API currently mounted by `backend/config/urls.py` and consumed by the Next.js frontend. Endpoint behavior is implemented primarily in `backend/core/views.py`; domain URL modules route to those views.

## Conventions

- Base path: `/api/`. The Next.js app proxies `/api/*` to Django.
- Request and response bodies use JSON. Public field names are camelCase.
- Dates use ISO `YYYY-MM-DD`; date-time labels are returned as strings. `Trade.executedAt` is formatted as `YYYY-MM-DDTHH:MM:SS` in the server's local time, without a timezone suffix.
- Successful reads and writes usually return `200`; creates return `201`; successful deletes may return `204`.
- Errors use `{"error":"..."}` and may include `errors`, `code`, or `field`. Validation errors return `400`; unauthenticated requests return `401`; permission failures return `403`.
- Company-scoped endpoints generally return `403` for an unknown or inaccessible company. Ticket detail/message/status endpoints return `404` when a ticket is missing or outside the caller's company access.
- Authentication uses Django's session cookie. Call `GET /api/auth/csrf/` to obtain the CSRF cookie/token, then send `X-CSRFToken` on unsafe requests.
- The server derives role and company access from stored user and company-access records; clients should not treat UI role gates as authorization.
- Roles are `admin`, `guest`, `client` (one or zero assigned companies), and `multi` (more than one assigned company). User kinds are `admin`, `client`, `colleague`, and `guest`.

## Main response shapes

- **Me:** `{id, name, first, last, email, kind, role, isOwner, companies, manages, allowed, tenantEmail, status}`. Admins have an empty `companies` list and all company IDs in `allowed` and `manages`.
- **Company:** `{id, name, legal, exch, code, price, vol30, spread30, trades30, value30, feed, last, timTarget, sprTarget, fee, shares, float, insiders, institutions, email, phone, address, custom, hasData}`. `feed` is `[state, label]`; `value30`, `last`, and `fee` are currently returned as `null`. `hasData` is true when at least one KPI row exists.
- **KPI:** `{kpi, market, contractStartIso}`. `kpi` contains the stored periods (`24h`, `7d`, `30d`, `since`); the `since` values do not include delta fields. `market` and `contractStartIso` may be `null`.
- **Peer group:** `{id, name, n, median, range, lo, hi}`; each array is ordered volume, spread, time, turnover.
- **Subscription:** `{none, plan, term, startIso, endIso, renewIso, status, autoRenew, services}`. `status` is `[kind,label]`; each service is `[name,scope]`. A missing subscription is represented by `none:true`. Renewal status uses the current server date.
- **Report:** `{title, period, publishedIso, href}`.
- **Trade:** `{id, executedAt, side, shares, price, value, venue}`.
- **Statement:** `{document, period, issuedIso, amount, statusKind, statusLabel}`.
- **Team member:** `{id, name, email, kind, isOwner, companies, companyCount, manages, status, via, token}`.
- **Admin user:** `{id, name, first, last, email, kind, isOwner, companies, manages, status, via, invitedBy, ownerName, token}`.
- **Signup link:** `{id, token, companies, createdIso, expiresIso, status, state, usedOnIso, usedBy, usedByName, createdBy}`. `status` and `state` contain the computed state.
- **Access request:** `{id, name, email, company, message, dateIso, status, linkId, matchedCompanyId}`.
- **Profile review:** `{id, company, status, submittedOnIso, by, changes, reviewedOnIso, reviewedBy, note}`. Changed fields are `legal`, `exch`, `shares`, `float`, `insiders`, `institutions`, `email`, `phone`, and `address`.
- **Ticket:** `{id, subject, company, by, status, createdIso, created, updatedLabel, messages}`. Each message contains `{from, name, at, atLabel, text}`.
- **Feed:** `{company, name, latest, expected, records, status}`.

## Endpoints

### Public and session endpoints

| Method and path | Behavior |
| --- | --- |
| `GET /api/meta/` | Returns `{today, demoMode}` using the configured reference date and demo-mode setting. |
| `GET /api/demo/samples/` | Returns sample `{signupToken, guestToken}` values when demo mode is enabled; returns `404` otherwise. Either token may be `null`. |
| `GET /api/auth/csrf/` | Returns `{csrfToken}` and sets the CSRF cookie. |
| `POST /api/auth/login/` | Accepts `{email,password,remember?}`; returns `{user: Me}` and starts a session. |
| `POST /api/auth/logout/` | Ends the current session; returns `204`. |
| `GET /api/auth/me/` | Returns `{user: Me|null}`. |
| `PATCH /api/auth/account/` | Signed-in user updates `{first,last,email}`; returns `{user: Me}` or validation errors. |
| `POST /api/auth/password/change/` | Signed-in user submits `{current,next,confirm}`; passwords must be at least 12 characters. Success returns `204` and preserves the session. |
| `POST /api/auth/password/reset/` | Accepts `{email}` and returns `{}` regardless of whether an active account exists. In local development, reset mail is written to the console. |
| `POST /api/auth/password/reset/confirm/` | Accepts `{uid,token,password,confirm}`; success returns `204`. |
| `GET /api/signup/{token}/` | Checks a pending invitation or sign-up link. Returns its state and, when open, the associated company details. |
| `POST /api/signup/{token}/` | Accepts `{name,password,confirm}` for an invitation, plus `email` for a sign-up link. Creates/activates the account and signs it in; returns `{user: Me}` with `201`. |
| `POST /api/access-requests/` | Accepts `{name,email,company?,message?}`; creates an access request and returns `{}` with `201`. |

### Company and client workspace endpoints

| Method and path | Behavior |
| --- | --- |
| `GET /api/companies/` | Lists companies visible to the caller, ordered by position and ID. |
| `POST /api/companies/` | Admin only. Creates a company from profile, contact, and optional KPI/feed fields; `name`, `exch`, and `code` are required. Returns a `Company` with `201`. |
| `GET /api/companies/{companyId}/kpi/` | Returns the company's KPI payload. Returns `404` with code `no_data` when no KPI rows exist. |
| `GET /api/companies/{companyId}/trades/` | Returns `{total,results}`. Optional query parameters: `from`, `to`, `side` (`All trades`, `Buy`, or `Sell`), and `q`; search checks the trade reference and venue. |
| `GET /api/companies/{companyId}/statements/` | Returns the company's statements. Guests receive `403`. |
| `GET /api/companies/{companyId}/profile-reviews/` | Returns `{pending,lastDecision}`. Guests receive both values as `null`. |
| `POST /api/companies/{companyId}/profile-reviews/` | Company manager submits `{values:{...profileFields}}`; returns the created review with `201`. A request with no changed fields returns `400`. |
| `DELETE /api/companies/{companyId}/profile-reviews/pending/` | Company manager withdraws the pending review; returns `204` or `400` if none exists. |
| `GET /api/companies/{companyId}/team/` | Returns `{members,managers}`. Guests receive `403`. |
| `POST /api/team/invitations/` | Non-guest callers may invite a `colleague` or `guest` with `{name,email,type,companies}`. Non-admin callers must manage each selected company. Returns a `TeamMember` with `201`. |
| `PUT /api/team/members/{personId}/access/` | Updates a member's `{companies}` access; returns `{}`. |
| `DELETE /api/team/members/{personId}/?company={companyId}` | Removes access to the specified company; without `company`, removes access within the caller's manageable scope (admins use all companies). Returns `{deleted}`. |
| `GET /api/peer-groups/` | Returns the available anonymized peer-group aggregates. |
| `GET /api/reports/` | Returns the report list. |
| `GET /api/subscriptions/` | Returns subscriptions keyed by visible company ID. Guests receive `403`. |
| `GET /api/tickets/` | Returns tickets for visible companies. Guests receive `403`; admins can see all tickets. |
| `POST /api/tickets/` | Client or multi-company user creates `{subject,company,message}`; returns a `Ticket` with `201`. |
| `GET /api/tickets/{ticketId}/` | Returns one visible ticket; inaccessible or missing tickets return `404`. |
| `POST /api/tickets/{ticketId}/messages/` | Adds `{text}` to a visible ticket. Admin messages are sent as support; guests cannot send messages. Returns the updated `Ticket` with `201`. |
| `POST /api/tickets/{ticketId}/status/` | Sets `{status:"done"|"ours"}` on a visible ticket; returns the updated `Ticket`. |

### Administration endpoints

All administration endpoints below require the admin role.

| Method and path | Behavior |
| --- | --- |
| `GET /api/admin/counts/` | Returns `{accessRequestsPending,profileReviewsPending}`. |
| `GET /api/admin/users/` | Returns the user list using the `Admin user` shape. |
| `PUT /api/admin/users/{personId}/access/` | Accepts `{companies,manages}` and updates company access. Returns `{}`. |
| `DELETE /api/admin/users/{personId}/` | Removes an eligible user; returns `204`. Active admin accounts and the caller's own account cannot be removed here. |
| `POST /api/admin/users/admins/` | Accepts `{first,last,email}` and creates a pending admin invitation; returns an `Admin user` with `201`. |
| `GET /api/admin/signup-links/` | Returns sign-up links, newest first. |
| `POST /api/admin/signup-links/` | Accepts `{companies,days,requestId?}` where `days` is 1–90; creates a link and returns it with `201`. |
| `POST /api/admin/signup-links/{linkId}/revoke/` | Revokes an unused link; returns the updated link. |
| `GET /api/admin/access-requests/` | Returns access requests, newest first. `matchedCompanyId` matches a company name, legal name, or ticker after punctuation/spacing normalization. |
| `POST /api/admin/access-requests/{requestId}/decision/` | Accepts `{decision:"approve"|"reject"}` and returns the updated request. |
| `GET /api/admin/profile-reviews/` | Returns profile reviews, newest first. |
| `POST /api/admin/profile-reviews/{reviewId}/decision/` | Accepts `{decision:"approve"|"reject",note?}`; approving applies the proposed fields to the company. |
| `PUT /api/admin/subscriptions/{companyId}/` | Creates or updates `{plan,term,startIso,renewIso,autoRenew,services}`. Renewal must follow the start date; `endIso` is the day before renewal. |
| `GET /api/admin/feeds/` | Returns the feed-status list. |
| `GET /api/admin/access-log/?q=&page=1&size=10` | Returns `{total,filteredTotal,page,pages,results}`. Each result contains `{stamp,first,last,email,company}`. |

## API documentation

The backend exposes an OpenAPI schema at `/api/schema/` and Swagger UI at `/api/docs/`. Access is public in debug mode and admin-only otherwise, according to `API_DOCS_PUBLIC`.
