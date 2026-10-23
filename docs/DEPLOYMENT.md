# Deployment

This is the runbook for putting NextStep on Render. The blueprint is `infra/render.yaml`. Read section 2 before the first deploy, because the API cannot start in production yet.

## 1. What is ready and what is not

| Part | Status | Notes |
|---|---|---|
| `ypp-web`, the public site (static) | **Ready** | Builds with `pnpm build`. Security headers set. Deep links rewrite to the app. Member pages hidden until the API is live. |
| `ypp-api`, the REST API (Python) | **Blocked** | Refuses to start with `APP_ENV=production`, because the Postgres store does not exist. The blueprint block is commented out. |
| Member sign-in | **Blocked** | Profiles use a browser token, which is not safe to expose (PROFILES.md §4). |
| Legal text and contact details | **Blocked** | Draft pages with placeholders (section 5). |

Deploy the site first. It works on its own, and the member links stay hidden until you switch them on.

## 2. Deploy the site

1. In Render, create a Blueprint from this repository. Render reads `infra/render.yaml`.
2. Confirm the `ypp-web` plan and region. Choose a region close to most users (ARCHITECTURE.md §3).
3. Leave `VITE_MEMBER_PAGES` at `"false"`.
4. Deploy. The build installs pnpm 12.15.0, runs `pnpm install --frozen-lockfile`, then `pnpm build`.
5. Add the custom domain in the Render dashboard, then run the smoke tests in section 6.

The `/v1/*` rewrite points at `api.example.invalid` on purpose. That host never resolves, so any member call fails with a clear error instead of reaching someone else's server. Replace it when the API is deployed (section 4).

## 3. Environment variables

The site needs no secrets. Everything it reads is set at build time.

| Variable | Set where | Value | Why |
|---|---|---|---|
| `NODE_VERSION` | `render.yaml` | `22` | Vite 8 needs Node 20.19 or 22.12+ |
| `VITE_MEMBER_PAGES` | `render.yaml` | `"false"` until the API is live | Shows the "My matches" link and the CV call to action |

The API will need these, set in the Render dashboard, never in the repository:

| Variable | Value | Notes |
|---|---|---|
| `APP_ENV` | `production` | Switches on the production checks |
| `DATABASE_URL` | from the Render Postgres instance | Required in production (`core/settings.py`) |
| `YPP_INGEST_CONTACT` | a monitored address | Sent to job boards with each fetch |
| `MATCH_MIN_SCORE_DEFAULT` | `40` | Product default for search |
| `EMBEDDING_PROVIDER` | `none` until an adapter exists | Scores are provisional without it (PROFILES.md §6) |
| `LLM_PROVIDER` | `none` | No LLM adapter is built |

`backend/.env` is ignored by git. Do not commit it.

## 4. Deploy the API, once it can run

Do not enable the API until every item in this list is done.

**Code blockers**

- [ ] **Postgres store.** Replace `InMemoryStore` with a Postgres implementation of the `Store` protocol (`core/ports.py`), following DATABASE.md. Candidates, listings, skills, and audit must all persist. Today a restart loses every profile.
- [ ] **Persistent audit.** `InMemoryAuditSink` loses the audit trail on restart. Write to `audit_log` (DATABASE.md §4).
- [ ] **Listings in production.** The demo snapshot loads only in `dev` and `demo` (`EnvironmentGuard`). Production needs the ingestion pipeline (TECHNICAL.md §14, phase 2a) to write real listings into Postgres, or the directory is empty.
- [ ] **Real sessions.** Replace `SessionTokens` (`backend/api/auth.py`) with the authentication design in ARCHITECTURE.md §7 and DESIGN.md §4.6. Tokens should expire and be revocable.
- [ ] **Rate limiting** on `POST /v1/profiles` and on CV upload. Each request creates an account and parses a file of up to 5 MB. Put a per-address limit in front of it.
- [ ] **Embedding adapter** for the semantic score term, or accept that scores stay provisional (PROFILES.md §6).

**Platform checks**

- [ ] **Python version.** README.md says Python 3.12. The tests here run on 3.14, and `infra/render.yaml` pins `PYTHON_VERSION` to 3.14. Pick one, run the full test suite on it, and update both places.
- [ ] **Proxy headers.** The start command passes `--proxy-headers --forwarded-allow-ips='*'`. That is safe only behind Render's proxy. Do not run the API on a public port without a proxy.
- [ ] **Health check** at `/v1/health` (already in the blueprint).

**Switching it on**

1. Uncomment the `ypp-api` block in `infra/render.yaml`, and set `DATABASE_URL` in the dashboard.
2. Deploy the API first, and check `/v1/health` on its own URL.
3. Replace `api.example.invalid` in the `/v1/*` rewrite with the API's host, and redeploy the site.
4. Set `VITE_MEMBER_PAGES` to `"true"` and redeploy the site.
5. Run the smoke tests in section 6, including a real CV upload.

## 5. Content to finish before launch

These are visible on the live site or in its legal text.

| Where | What to fill in |
|---|---|
| `src/pages/LegalPages.tsx` | Contact address for privacy questions |
| `src/pages/LegalPages.tsx` | Date of the last change to the terms |
| `src/pages/LegalPages.tsx` | Accessibility contact for reporting barriers |
| `src/pages/LegalPages.tsx` | Counsel review. Every legal page carries a draft notice until this is done |
| `public/images/CREDITS.md` | Photographer names, if your attribution policy needs them |
| `docs/ARCHITECTURE.md` §7, `docs/DATABASE.md` §4 (retention lines) | Retention windows, to be confirmed with counsel |
| `docs/TECHNICAL.md` §6 | Evidence weighting, to be confirmed against the gold set |
| `src/pages/StandardsPage.tsx` | Confirm the "not yet in place" list still matches reality on launch day |

Remove the draft notice from the legal pages only after counsel signs off.

## 6. Smoke tests

Run these after every deploy. Replace `https://your-domain` with the live address.

```bash
# Site loads, and deep links work
curl -sI https://your-domain/ | grep -i "^HTTP\|content-security-policy\|strict-transport"
curl -sI https://your-domain/opportunities/anything | grep -i "^HTTP"        # expect 200 (SPA fallback)

# Security headers present
curl -sI https://your-domain/ | grep -i "x-content-type-options\|referrer-policy\|permissions-policy"

# Static assets served with the right type
curl -sI https://your-domain/data/opportunities.json | grep -i "^HTTP\|content-type"

# Once the API is live
curl -s https://your-domain/v1/health                                      # {"status":"ok"}
curl -si https://your-domain/v1/me/profile | grep -i "^HTTP\|cache-control" # 401, no-store
```

In a browser, check:

- The landing page loads with no console errors, and its images show.
- `/opportunities` filters and opens a listing.
- `/opportunities/does-not-exist` shows "Listing not found".
- `/nope` shows the 404 page.
- Member links are absent until `VITE_MEMBER_PAGES` is `"true"`.
- After enabling them: upload a CV, see the dashboard, delete the profile.

## 7. Rollback

- **Site:** in the Render dashboard, redeploy the previous successful deploy. The site is stateless.
- **API:** the same, once it exists. Before it has a database, rolling back is the only fix for a bad release, and it also empties profiles. Plan the database migration rollback before the first production deploy.

## 8. Known gaps after launch

- No error tracking. Add one before traffic arrives, so failures are visible.
- No uptime monitoring beyond Render's health checks.
- The site has no analytics. This is deliberate, and the privacy notice says so. Changing it means updating the notice first.
- Fonts are about 400 KB of woff2 files. A Latin-only build would cut this (docs/FRONTEND.md §12).
- The production CSP allows only `'self'`. Any new third-party script, font, or image host needs a header change in `infra/render.yaml`.
