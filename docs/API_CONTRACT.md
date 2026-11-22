# Deltablock REST API contract (backend <-> frontend)

Single source of truth shared by the Django backend and the Next.js frontend.
Base path: `/api/` (the Next.js app proxies `/api/*` to Django, so cookies are same-origin).
All bodies are JSON, all keys **camelCase** exactly as written below. Dates are ISO `YYYY-MM-DD`; datetimes ISO 8601.
Auth: Django session cookie + CSRF (`X-CSRFToken` header on every unsafe method; token cookie set by `GET /api/auth/csrf/`).

## Conventions
* Success: 200/201 with the JSON shown. `204` for deletes.
* Validation failure: `400 {"error": "<message>", "errors": {"<field>": "<message>"} (optional), "code": "<code>" (optional), "field": "<field>" (optional)}`
* `401 {"error": "Authentication required."}` not signed in, `403 {"error":"..."}` signed in but not allowed, `404 {"error":"..."}` missing **or not visible to the caller** (tenant isolation: never reveal another company's records).
* The server never trusts role / company / owner values from the client. Role, company access and manager rights always come from the database.
* "visible company" = admin: every company; everyone else: the companies in their access list.
* Roles (`role`): `client` (non-admin, non-guest, 1 company), `multi` (non-admin, non-guest, >1 company), `guest`, `admin`. Derived from the person: `kind admin -> admin`, `kind guest -> guest`, else `multi` if companies>1 else `client`. Person `kind`s: `admin|client|colleague|guest`.
* `canManage(company)` = role != guest and company in `manages` (admin manages every company). `canEditProfile(company)` = role not in (admin, guest) and company in `manages`.
* Display strings (month labels such as `23 Oct 2026`) are produced by the frontend from ISO dates, EXCEPT the free-text labels the original stored as text (`updatedLabel`, `atLabel`) which are stored and returned as text.

## Object shapes
**Me**: `{id, name, first, last, email, kind, role, isOwner, companies:[companyId], manages:[companyId], allowed:[companyId], tenantEmail|null, status}`
(`allowed` = visible company ids; for admin `companies` is `[]`, `allowed` and `manages` are every company id.)

**Company**: `{id, name, legal, exch, code, price|null, vol30|null, spread30|null, trades30|null, value30|null, feed:[kind,label], last|null, timTarget|null, sprTarget|null, fee|null, shares, float, insiders, institutions, email, phone, address, custom:bool, hasData:bool}` (`id` is the slug: `c1`, `c2`, `elite`, ...; strings may be `""`; `feed.kind` in `ok|warn|dr`). `hasData` = a KPI set exists.

**KPI payload** `GET /api/companies/{id}/kpi/` -> `{kpi:{"24h":{tim,timD,vol,volD,spr,sprD,turn,turnD,share,traders},"7d":{...},"30d":{...},"since":{tim,vol,spr,turn,share,traders}}, market:{marketTrades30,buyPct}|null, contractStartIso|null}`; `404 {"code":"no_data"}` when the company has no KPI rows. (`contractStartIso` = that company's subscription start date; sent to every role including guests because Market activity uses it.)

**PeerGroup**: `{id,name,n,median:[vol,spr,tim,turn],range:[s,s,s,s],lo:[4 numbers],hi:[4 numbers]}`

**Subscription** (`GET /api/subscriptions/` -> object keyed by visible company id; non-guest only; company without row => `{"none":true,"plan":"Not assigned","term":"—","startIso":null,"endIso":null,"renewIso":null,"status":["dr","Not assigned"],"autoRenew":"","services":[]}`): `{none:false, plan, term, startIso, endIso, renewIso, status:[kind,label], autoRenew, services:[[name,scope],...]}`

**Report**: `{title, period, publishedIso, href}` with `href` like `/reports/monthly-liquidity-review.pdf`.

**Trade**: `{id, executedAt:"2026-10-23T14:22:00", side:"Buy|Sell", shares, price, value, venue}` (`value = shares*price` unrounded).

**Statement**: `{document, period, issuedIso, amount, statusKind, statusLabel}`

**TeamMember**: `{id, name, email, kind, isOwner, companies:[ids visible to caller], companyCount, manages:[ids visible to caller], status:"active|pending", token|null}` (`token` only when caller canManage the company and member is pending).
**User (admin list)**: `{id, name, first, last, email, kind, isOwner, companies:[ids], manages:[ids], status, via, invitedBy, ownerName, token|null}` (`ownerName` = name of the account owner of the person's tenant if that is a different person else `""`; `token` only for pending persons).

**SignupLink**: `{id:"L5", token, companies:[ids], createdIso, expiresIso, status:"unused|used|expired", state:"unused|used|expired", usedOnIso|null, usedBy, usedByName, createdBy}` (`state` computed server-side: used->used, status expired->expired, expiresIso < today (server local date)->expired, else unused).
**AccessRequest**: `{id:"R4", name, email, company, message, dateIso, status:"pending|approved|rejected", linkId|null, matchedCompanyId|null}` (`matchedCompanyId` = company whose name, legal name or code equals the typed company text, case/space-insensitive).
**ProfileReview**: `{id:"PR101", company, status:"pending|approved|rejected|withdrawn", submittedOnIso, by:{name,email}, changes:{"<field>":{from,to}}, reviewedOnIso|null, reviewedBy:{name,email}|null, note}`; fields are `legal, exch, shares, float, insiders, institutions, email, phone, address`.
**Ticket**: `{id:"DB-1052", subject, company, by, status:"ours|client|done", createdIso, updatedLabel, messages:[{from:"client|support", name, atLabel, text}]}`
**Feed**: `{company, name, latest, expected, records, status:[kind,label]}`

## Endpoints
### Meta / config
* `GET /api/meta/` -> `{today:"2026-10-23", demoMode:bool}`  (`today` = fixed demo reference date used by the original for renewal countdowns and the market model)
* `GET /api/demo/samples/` -> `{signupToken|null, guestToken|null}` only when `DEMO_MODE`, else 404 (powers the original "open a sample ... link" hints)

### Auth (no sign-in needed unless stated)
* `GET /api/auth/csrf/` -> `{csrfToken}` and sets the csrftoken cookie
* `POST /api/auth/login/ {email,password}` -> `{user: Me}` | 400 `{error}`. Unknown email: "No account uses that email address. Ask your administrator, or request access." Pending account: "That account has not been set up yet. Open the invitation link you were given." Wrong password: "The email or password is not correct."
* `POST /api/auth/logout/` -> 204
* `GET /api/auth/me/` -> `{user: Me|null}` (always 200)
* `PATCH /api/auth/account/ {first,last,email}` (signed in) -> `{user: Me}` | 400 `{errors:{first,last,email}, error:"Please fix the highlighted fields."}`. Messages: "Enter your first name.", "Use at most 60 characters.", "Enter your last name.", "Enter a valid email address.", "Another account already uses this email address."  Changing email re-points tenant/invitedBy/link `usedBy`/review `by` references.
* `POST /api/auth/password/change/ {current,next,confirm}` (signed in) -> 204 | 400 `{errors:{current|next|confirm}, error:"Your password was not changed. Please check the highlighted fields."}`. "Enter your current password.", "The current password is not correct.", password rule below, "Choose a password that is different from the current one." Keeps the session alive (update_session_auth_hash).
* `POST /api/auth/password/reset/ {email}` -> always 200 `{}`; if an active account exists a reset e-mail is sent (console backend in dev).
* `POST /api/auth/password/reset/confirm/ {uid,token,password,confirm}` -> 204 | 400  (backend-only; the original UI has no page for it)
* Password rule: min 12 chars ("Use at least 12 characters for the password."), must match confirm ("The two passwords do not match.").

### Sign-up links and invitations (public, token based)
* `GET /api/signup/{token}/` ->
  * `{state:"invalid"}`
  * link: `{state:"used", usedOnIso}` | `{state:"expired"}` | `{state:"no_companies"}` | `{state:"open", kind:"link", companies:[{id,name,exch}]}`
  * invitation (a pending person has this token): `{state:"invite_used"}` if the person is no longer pending, else `{state:"open", kind:"invite", inviteType:"colleague|guest|admin", name, email, invitedBy, companies:[{id,name,exch}]}`
* `POST /api/signup/{token}/ {name,email,password,confirm}` -> 201 `{user: Me}` and the new session is signed in. 400 `{code:"invalid|used|expired|field|duplicate", field?, error}`; messages exactly as the original: "This sign-up link is not valid.", "This link was already used.", "This link has expired.", "Enter your name.", "Enter a valid email address.", the duplicate message "An account with this email address already exists. Please log in to continue. If you need access to another company, contact your administrator.", "This invitation is not valid or was already used.", "The companies for this link no longer exist. Ask your administrator for a new link." For invitations `email` is ignored (the invited address is used). Link registration creates a `client` person, owner, access+manage on all link companies, tenant = themselves, via "Sign-up link", marks link used.
* `POST /api/access-requests/ {name,email,company,message}` (public, throttled) -> 201 `{}`

### Companies and company-scoped data (signed in)
* `GET /api/companies/` -> `[Company]` visible companies, ordered by creation (seed order).
* `POST /api/companies/` (admin) -> 201 `Company` | 400 `{errors:{...}, error:"Please fix the highlighted fields."}` — body `{name,legal,exch,code,email,phone,address,shares,float,insiders,institutions,price,vol30,spread30,feed:"none|ok|warn"}`; validation + messages exactly as the original `createCompany` in `js/app.js`.
* `GET /api/companies/{id}/kpi/` (visible) -> KPI payload.
* `GET /api/peer-groups/` -> `[PeerGroup]`
* `GET /api/reports/` -> `[Report]`
* `GET /api/companies/{id}/trades/?from=YYYY-MM-DD&to=YYYY-MM-DD&side=All trades|Buy|Sell&q=text` -> `{total, results:[Trade]}`; `total` = number of stored trades for the company (unfiltered); results filtered by executed date between from/to inclusive, side, and q substring (case-insensitive) of `"<id> <venue>"`, ordered by seq.
* `GET /api/companies/{id}/statements/` (client, multi, admin; guest 403) -> `[Statement]` (empty if none)
* `GET /api/subscriptions/` (non-guest) -> `{<companyId>: Subscription}` for every visible company
* `GET /api/companies/{id}/team/` (client, multi, admin; guest 403; visible company) -> `{members:[TeamMember], managers:[name]}`; members = non-admin persons with access to the company who are active, or pending team invites (`via == "Team invite"`); sorted managers first then by name; `managers` = names of active non-admin persons that manage the company. Each member's `companies`/`manages` are restricted to the caller's visible companies (admin sees all).
* `GET /api/companies/{id}/profile-reviews/` (visible) -> `{pending: ProfileReview|null, lastDecision: ProfileReview|null}`; guests always get both null. `lastDecision` = newest approved or rejected.
* `POST /api/companies/{id}/profile-reviews/ {values:{legal,exch,shares,float,insiders,institutions,email,phone,address}}` (canEditProfile) -> 201 ProfileReview | 400 `{errors, error}` (messages exactly as original `submitProfile`, plus 400 `{error:"Nothing has changed compared with the approved profile."}`); replaces the company's existing pending request.
* `DELETE /api/companies/{id}/profile-reviews/pending/` (canEditProfile) -> 204 (marks it `withdrawn`) | 400 `{error:"There is nothing pending."}`
* `GET /api/tickets/` -> `[Ticket]` visible (admin all; guest 403), newest first.
* `POST /api/tickets/ {subject,company,message}` (client/multi; admin & guest 403) -> 201 Ticket; id = `DB-` + 4 digit number (max existing, at least 1052, +1); status `ours`; first message from client.
* `GET /api/tickets/{id}/` -> Ticket | 404
* `POST /api/tickets/{id}/messages/ {text}` -> 201 Ticket. admin: sender support, name `"<admin name> · Deltablock support"`, status -> `client`; others: sender client, name = user name, status -> `ours`. `updatedLabel` = `Today, HH:MM`, message `atLabel` = `Today · HH:MM` (server local time).
* `POST /api/tickets/{id}/status/ {status:"done"|"ours"}` -> Ticket; sets `updatedLabel`.

### Team management (client/multi managers; admin)
* `POST /api/team/invitations/ {name,email,type:"colleague|guest",companies:[ids]}` -> 201 TeamMember(+token). Rules from original `inviteMember` (guest forbidden, valid email, at least one company, every company must be managed by caller, email must be new: "That email already has an account or an invitation. An administrator can add company access from Users → Edit access."); invited person: status pending, via "Team invite", invitedBy caller, tenant = caller's tenant, token `<type>-<random>`.
* `PUT /api/team/members/{personId}/access/ {companies:[ids]}` -> 200 `{}`; original `updateMemberAccess` + `memberGuard` rules/messages.
* `DELETE /api/team/members/{personId}/?company={id}` -> 200 `{deleted:bool}`; original `removeMember` rules (person is deleted when they have no company left).

### Admin (role admin only; else 403)
* `GET /api/admin/counts/` -> `{accessRequestsPending, profileReviewsPending}`
* `GET /api/admin/users/` -> `[User]` ; `PUT /api/admin/users/{id}/access/ {companies,manages}` -> `{}` (original `setAccessAdmin`); `DELETE /api/admin/users/{id}/` -> 204 (original `removePerson` rules); `POST /api/admin/users/admins/ {first,last,email}` -> 201 `User` | 400 `{field, error}` (original `addAdmin`).
* `GET /api/admin/signup-links/` -> `[SignupLink]` newest first; `POST /api/admin/signup-links/ {companies,days,requestId?}` -> 201 SignupLink (days 1-90; messages "Choose at least one company.", "Choose how long the link stays valid."; if `requestId` names an *approved* request, it is linked to the new link); `POST /api/admin/signup-links/{id}/revoke/` -> 200 SignupLink (only unused links, else 400 "Only unused links can be revoked.").
* `GET /api/admin/access-requests/` -> `[AccessRequest]` newest first; `POST /api/admin/access-requests/{id}/decision/ {decision:"approve"|"reject"}` -> AccessRequest (only pending, else 400).
* `GET /api/admin/profile-reviews/` -> `[ProfileReview]` newest first; `POST /api/admin/profile-reviews/{id}/decision/ {decision:"approve"|"reject", note}` -> ProfileReview; approve writes the values onto the Company; 400 for non-pending ("This request has already been <status>."), reviewing your own request ("You cannot review your own request."), unknown decision.
* `PUT /api/admin/subscriptions/{companyId}/ {plan,term,startIso,renewIso,autoRenew,services:[[name,scope]]}` -> Subscription. Rules from original: renewIso > startIso ("Renewal date must be after the start date."), term required ("Enter the service term."), services may not be website page names ("“X” is a website page, not a contracted service. Remove it from the list."), endIso = renewIso - 1 day, status = expired (`bad`,"Expired") if renew < demo today, "Renews soon" (`warn`) if <= 60 days else "Active" (`ok`); plan in `Liquidity Essentials|Liquidity Plus|Investor Relations`. Creates the subscription if none.
* `GET /api/admin/feeds/` -> `[Feed]`
* `GET /api/admin/access-log/?q=text&page=1&size=10` -> `{total, filteredTotal, page, pages, results:[{stamp,first,last,email,company}]}`; `stamp` e.g. `Thu 22 Oct 2026 08:41 am`; every whitespace-separated word of `q` must be a substring (case-insensitive) of `"<stamp> | <YYYY-MM-DD HH:MM> | <first> | <last> | <first last> | <email> | <company>"`.
