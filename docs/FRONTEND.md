# Frontend

This document describes the web front end of Youth Yellow Pages: what it does, how it is built, how it gets its data, how it is tested and how it is deployed. For the backend and the rest of the system see [ARCHITECTURE.md](ARCHITECTURE.md) and [TECHNICAL.md](TECHNICAL.md).

## 1. Scope

The web app is a single-page React application at the root of the repository. In this phase it lets a visitor browse opportunities across Nigeria, South Africa, Kenya and Ghana, filter them, and follow each listing to the employer's original posting.

It does not yet:

- call the REST API (`/v1` is not built),
- sign users in or hold profiles,
- show ranked talent matches or explanations (these come from the MCP and REST layers later),
- support the mobile app (Flutter, planned separately).

## 2. Stack

| Concern | Choice | Notes |
|---|---|---|
| Language | TypeScript (`strict` mode) | `typescript@7` runs `tsc -b` for the typecheck |
| UI library | React 19 | `StrictMode` enabled in `src/main.tsx` |
| Build and dev server | Vite 8 with `@vitejs/plugin-react` 6 | Output in `dist/` |
| Package manager | pnpm 12.15.0 | Pinned by `packageManager` and `devEngines` in `package.json`; `pnpm-lock.yaml` is committed |
| Tests | Vitest 5, Testing Library, jsdom, `@testing-library/jest-dom` | Runs in jsdom, no browser needed |
| Styling | Plain CSS in `src/styles.css` | No CSS framework; custom properties at `:root` hold the palette |
| Runtime requirement | Node.js `^20.19.0 \|\| >=22.12.0` | Set in `engines`, which Vite 8 requires |

No router, state library or UI kit is used. The app has one screen, and its state lives in `App.tsx`.

## 3. Repository layout

Frontend files sit at the root, next to `backend/`:

```
.
├── index.html               Document shell; mounts #root and loads src/main.tsx
├── package.json             Scripts, dependencies, Node and pnpm requirements
├── pnpm-lock.yaml           Locked dependency tree (commit this)
├── vite.config.ts           React plugin, dev and preview ports, Vitest settings
├── tsconfig.json            Strict TypeScript for src/ and vite.config.ts
├── public/
│   ├── favicon.svg          Site icon
│   └── data/
│       └── opportunities.json   Static data snapshot (see section 5)
├── src/
│   ├── main.tsx             Entry point: creates the React root
│   ├── App.tsx              Page layout, data loading, filter state, paging
│   ├── App.test.tsx         Renders App against a mocked fetch
│   ├── styles.css           All styles
│   ├── test-setup.ts        Loads the jest-dom matchers for Vitest
│   ├── components/
│   │   ├── FilterBar.tsx        Search box and three dropdowns, plus Clear filters
│   │   └── OpportunityCard.tsx  One listing: employer, title, tags, meta, link
│   └── lib/
│       ├── opportunities.ts       Types, labels, load, filter, sort, country list
│       └── opportunities.test.ts  Unit tests for the logic in lib/opportunities.ts
├── infra/
│   └── render.yaml          Render static-site blueprint
└── dist/                    Build output (git-ignored)
```

Keep the boundary clear: `lib/` holds pure logic with no React imports, and `components/` holds presentation only. `App.tsx` connects the two.

## 4. How the page works

1. **Load.** On mount, `App` calls `loadOpportunities` with `DATA_URL`, which is `${BASE_URL}data/opportunities.json`. The request is tied to an `AbortController`, so an unmount cancels it. The page has three states: `loading` (a status line), `error` (an alert with the message and a refresh hint) and `ready`.
2. **Filter.** `filterOpportunities` applies the four filters together (a listing must pass all of them):
   - **Search:** the query is trimmed, lowercased and split on whitespace. Each term must appear in the combined title, employer, department and location text. Descriptions are not searched.
   - **Country:** the listing's `eligible_countries` must contain the chosen code. Listings with no eligible countries only appear under "All countries".
   - **Work mode:** `remote` or `onsite_or_hybrid`.
   - **Eligibility (scope):** one of the five scope values in section 6.
3. **Sort.** `sortByUpdated` orders results by `updated_at`, newest first. It copies the array, so the loaded data is never mutated.
4. **Page.** `PAGE_SIZE` is 24. "Show more" adds another 24. Changing any filter resets the count to 24.
5. **Show.** Each card shows the employer, title, a work-mode tag, an eligibility tag, the eligible country codes, the location, the updated date and a "View original posting" link. The link opens in a new tab with `rel="noopener noreferrer"`.

The results line uses `aria-live="polite"`, so screen readers announce changes in the count. The search and dropdowns are real labelled controls.

## 5. Data

The app reads one static file, `public/data/opportunities.json`. It is a copy of `backend/demo/greenhouse_snapshot.json`, which holds public Greenhouse job-board data with HTML removed. Each listing names its employer and links to the original posting, which the file's own notice calls the source of truth.

Listing fields the front end uses:

| Field | Used for |
|---|---|
| `employer`, `title`, `department`, `location_text` | Card text and search |
| `description` | Card excerpt, shown as plain text and clamped to four lines by CSS |
| `eligible_countries` | Country filter and tags |
| `work_mode`, `scope` | Filters and tags |
| `updated_at` | Sort order and the date shown |
| `source_url` | The "View original posting" link |
| `source_key`, `external_id` | React list key (`source_key:external_id`) |

Fields the file carries but the front end does not use yet: `unmapped_locations`, `expires_at`, `pay_ranges`. The `fetched_at` timestamp is shown as "Listings last refreshed".

**Moving to the API.** When `/v1` exists, change `DATA_URL` in `src/App.tsx` to the endpoint, and keep the response shape matching `OpportunitySnapshot` in `src/lib/opportunities.ts`. Only `loadOpportunities` and the constant need to change. If the API paginates, the paging code in `App.tsx` must move to the server, which is a larger change.

Refresh the snapshot by running the connector in the backend, not by editing the JSON by hand.

## 6. Labels and fixed values

These come from TECHNICAL.md §14 and DATABASE.md, and the front end must not invent new ones.

| Value | Label shown |
|---|---|
| `work_mode: remote` | Remote |
| `work_mode: onsite_or_hybrid` | On-site or hybrid |
| `scope: in_region` | In your region |
| `scope: remote_in_region` | Remote, in your region |
| `scope: outside_region` | Not in your country |
| `scope: remote_outside_region` | Remote, not in your country |
| `scope: unspecified` | Eligibility unclear |

The types `WorkMode` and `Scope` are closed unions in `src/lib/opportunities.ts`. If the backend adds a value, add it there first, or the label lookup will return `undefined`.

## 7. Design rules

- **Plain text only.** Listing descriptions and titles are third-party text. They are rendered as text nodes and never through `dangerouslySetInnerHTML`.
- **Links go to the source.** The app shows and links to the employer's posting. It does not claim to hold or process applications.
- **No personal data.** The front end handles no names, contact details or profiles. Consistent with the contributing rules in the README, it adds no fields about age, gender, photos or school names.
- **Accessible by default.** Native form controls with visible labels, a visible focus outline (`:focus-visible`), a live region for counts, and a `prefers-reduced-motion` rule.
- **One source of filter logic.** Filtering and sorting live in `lib/` and nowhere else.

## 8. Commands

Run these from the repository root.

```bash
pnpm install        # install from pnpm-lock.yaml
pnpm dev            # dev server at http://localhost:5173
pnpm test           # vitest run, once
pnpm typecheck      # tsc -b, no emit
pnpm build          # typecheck, then vite build into dist/
pnpm preview        # serve dist/ at http://localhost:4173
```

Run `pnpm typecheck && pnpm test && pnpm build` before merging frontend changes.

## 9. Testing

| File | What it covers |
|---|---|
| `src/lib/opportunities.test.ts` | Each filter alone and combined; country matching against several codes; empty eligibility lists; multi-term search and case-insensitivity; sort order and no mutation; country list uniqueness and order |
| `src/App.test.tsx` | Page size of 24 and the Show more control; descriptions rendered as text; search narrows results, the empty state appears, and Clear filters restores them; an HTTP 500 shows the error alert |

Both files use the real components and logic. `App.test.tsx` replaces `fetch` with a stub and does not touch the network.

**Not covered yet:** visual layout, responsive behaviour on phones, and real-browser behaviour. Playwright or a similar browser test is the next step for those.

## 10. Deployment

`infra/render.yaml` defines a Render **static site** named `ypp-web`:

- **Build:** installs pnpm 12.15.0 globally, then runs `pnpm install --frozen-lockfile && pnpm build`.
- **Publish:** `./dist`.
- **Node:** `NODE_VERSION` is 22.
- **Headers on every path:**
  - `Content-Security-Policy`: `default-src 'self'`, with images allowing `data:`, scripts and styles limited to `'self'`, `connect-src 'self'`, `frame-ancestors 'none'`, `form-action 'none'`.
  - `Strict-Transport-Security`: one year, with `includeSubDomains`.
  - `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, and a `Permissions-Policy` that turns off camera, microphone and geolocation.

The CSP has no `style-src 'unsafe-inline'`. Do not add inline styles or inline scripts without updating the policy. When the API is added, `connect-src` must list its origin.

The site is a static single page with no client-side routes, so no rewrite rule is needed. Add one if routing is introduced.

## 11. Decisions

| Decision | Why | Trade-off |
|---|---|---|
| Vite instead of Next.js | The app is client-side only for now, with no server rendering or routing needs. The README originally named Next.js; the team chose React | No server rendering, so SEO for listings would need work later |
| Static snapshot data | The API does not exist yet, and a snapshot lets the page be deployed and reviewed now | Data is only as fresh as the last snapshot; loading 1.8 MB up front is heavy |
| Filtering on the client | With 272 listings the cost is negligible, and the logic is pure and easy to test | Must move to the server once listings are paginated by the API |
| No UI library | Keeps the bundle small (about 70 KB gzipped JavaScript) and the styles easy to change | More hand-written CSS |
| pnpm, with the version pinned | Reproducible installs; `--frozen-lockfile` in CI and on Render | Contributors need pnpm 12 |
| TypeScript 7 | Current release; `tsc -b` works in this setup | It is a major new version, so watch for tooling issues |

## 12. Known limits

- The data is a static snapshot and does not update on its own.
- The "View original posting" link relies on the employer's URL staying valid. A dead link is not detected.
- Expired listings are not hidden. `expires_at` is null in the current snapshot, so there is nothing to filter on yet.
- Long descriptions are clamped with CSS. Full text is not shown, and the card does not expand.
- The app is not tested in a real browser or on a phone. Accessibility has not been audited with a screen reader.

## 13. Next steps

1. Replace the static snapshot with the `/v1` listings endpoint, and move filtering and paging to the server.
2. Add a browser test (Playwright) for the main flow and a mobile viewport.
3. Show the eligibility reason on each card, using the scope and country data already in the listing.
4. Add a listing detail view, or open the description in a dialog.
5. Add the web service to `infra/render.yaml` alongside the API once the backend is deployable.
