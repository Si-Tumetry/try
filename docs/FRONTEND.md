# Frontend

This document describes the NextStep web front end: what it does, how it is built, where its data comes from, how it is tested, and how it is deployed. For the page designs see [../DESIGN.md](../DESIGN.md). For the backend see [ARCHITECTURE.md](ARCHITECTURE.md) and [TECHNICAL.md](TECHNICAL.md).

## 1. Scope

The web app is a React single-page application at the root of the repository. It serves the public part of NextStep:

| Route | Page | Data |
|---|---|---|
| `/` | Landing | Listings snapshot (counts, featured roles) |
| `/opportunities` | Directory with filters, sort and paging | Listings snapshot |
| `/opportunities/:id` | Opportunity detail | Listings snapshot |
| `/standards` | How listings are checked | Static |
| `/about` | About, with directory counts | Listings snapshot |
| `/privacy`, `/terms`, `/accessibility` | Draft legal pages | Static |
| `*` | Not found | None |

Not built yet, and designed in [DESIGN.md](../DESIGN.md): sign-in and sign-up, onboarding, my profile and matches, privacy controls, and every employer page. These need authentication and the REST API first.

## 2. Stack

| Concern | Choice | Notes |
|---|---|---|
| Language | TypeScript, `strict` | `typescript@7`; `pnpm typecheck` runs `tsc -b` |
| UI | React 19 | `StrictMode` in `src/main.tsx` |
| Routing | React Router 8, data router | `createBrowserRouter` in `src/App.tsx`; routes in `src/routes.tsx` |
| Styling | Tailwind CSS 4 through `@tailwindcss/vite` | Design tokens in the `@theme` block in `src/index.css` |
| Fonts | Newsreader and Plus Jakarta Sans, self-hosted through `@fontsource-variable` | Loaded from `src/main.tsx`; no external font requests |
| Icons | Inline SVG in `src/components/Icon.tsx` | No icon font |
| Build | Vite 8 with `@vitejs/plugin-react` 6 | Output in `dist/` |
| Package manager | pnpm 12.15.0 | Pinned in `packageManager` and `devEngines`; `pnpm-lock.yaml` is committed |
| Tests | Vitest 5, Testing Library, jsdom, jest-dom | No browser needed |
| Node | `^20.19.0 \|\| >=22.12.0` | Set in `engines`, as Vite 8 requires |

The Tailwind CDN in the design sample is not used. It loads script from outside the origin, which the Content-Security-Policy in `infra/render.yaml` blocks.

## 3. Repository layout

```
.
├── index.html                  Document shell; title "NextStep"
├── package.json
├── pnpm-lock.yaml
├── vite.config.ts              React and Tailwind plugins; dev and preview ports; Vitest settings
├── tsconfig.json
├── public/
│   ├── favicon.svg
│   └── data/opportunities.json Listings snapshot (see section 5)
├── src/
│   ├── main.tsx                Entry: fonts, global CSS, React root
│   ├── index.css               Tailwind import, @theme tokens, base styles, reduced-motion rules
│   ├── App.tsx                 Creates the browser router and renders RouterProvider
│   ├── routes.tsx              Route table (public routes only)
│   ├── App.test.tsx            Route-level tests against the real pages and a stubbed fetch
│   ├── test-setup.ts           Loads jest-dom matchers
│   ├── hooks/
│   │   ├── useOpportunities.ts Loads the snapshot; returns loading, error or ready
│   │   └── useDocumentTitle.ts Sets "<page> · NextStep"
│   ├── pages/
│   │   ├── Layout.tsx          Skip link, header, main outlet, footer
│   │   ├── LandingPage.tsx
│   │   ├── OpportunitiesPage.tsx
│   │   ├── OpportunityDetailPage.tsx
│   │   ├── StandardsPage.tsx
│   │   ├── AboutPage.tsx
│   │   ├── LegalPages.tsx      Privacy, terms and accessibility drafts
│   │   └── ErrorPages.tsx      404 and route error (500)
│   ├── components/
│   │   ├── PhotoBand.tsx       Full-width photograph under a blue overlay (strong or soft)
│   │   ├── SiteHeader.tsx      Header, navigation and Wordmark
│   │   ├── SiteFooter.tsx
│   │   ├── Section.tsx         Numbered section heading and Hairline
│   │   ├── ProsePage.tsx       Long-form page layout
│   │   ├── FilterBar.tsx       Search, sector, country, work mode and eligibility
│   │   ├── OpportunityCard.tsx
│   │   ├── EligibilityTag.tsx  Scope, work-mode and country tags
│   │   └── Icon.tsx
│   ├── lib/
│   │   ├── opportunities.ts    Types, labels, filter, sort, stats, loader and cache
│   │   ├── opportunities.test.ts
│   │   ├── sectors.ts          Sector definitions and matching
│   │   └── format.ts           Dates and counts
│   └── test/fixtures.ts        Fixed listings for tests
├── public/images/              Unsplash photographs with no people; see CREDITS.md
├── infra/render.yaml           Render static site and security headers
└── dist/                       Build output (git-ignored)
```

Layering: `lib/` holds pure logic with no React imports. `components/` holds presentation. `pages/` connects them to data and routes. Tests import the real modules.

## 4. How the pages work

**Data loading.** `useOpportunities` calls `getOpportunitySnapshot`, which fetches `data/opportunities.json` once per page session and shares the result between pages. A failed load is not cached, so a retry can succeed. Each page handles three states: loading, error (an alert with the message), and ready.

**Directory state lives in the URL.** `OpportunitiesPage` reads `q`, `country`, `workMode`, `scope`, `sector` and `sort` from the query string. Changing a filter updates the URL, so a search can be shared and the back button works. Typing in the search box replaces the history entry rather than adding one per keystroke. The page shows 24 results at a time. Changing any filter or the sort resets the count.

**Filtering rules** (`filterOpportunities`). A listing must pass every active filter:
- **Search:** the query is trimmed, lowercased and split on whitespace. Each term must appear in the title, employer, department or location. Descriptions are not searched.
- **Country:** the listing's `eligible_countries` must contain the code. Listings with no eligible countries appear only under "All countries".
- **Work mode** and **eligibility** match the listing's `work_mode` and `scope` exactly.
- **Sector:** see section 5.

**Sorting.** "Most recent" orders by `updated_at`, newest first. "Employer A to Z" orders by employer, then title. Sorting copies the array.

**Landing page.** The hero search and the quick-search links go to `/opportunities?q=…`. The sector cards go to `/opportunities?sector=…`. Featured roles are the three most recently updated listings open in a launch country. Every figure on the page is computed from the snapshot. No outcome, match-rate or response-time figures are shown, because nothing measures them yet.

**Opportunity detail.** The id is `source_key:external_id`, URL-encoded in the path. Descriptions are split into paragraphs on blank lines and shown as plain text. The apply button opens the employer's `source_url` in a new tab with `rel="noopener noreferrer"`. If `expires_at` is in the past, the apply button is replaced by an expiry notice. A missing id shows "Listing not found".

**Standards and About.** Static text. The eligibility labels on the standards page come from the same `SCOPE_LABELS` table the filters use, so they cannot drift.

**Legal pages** are drafts. Each carries a visible notice and bracketed placeholders, such as the contact address, that must be filled in before launch.

## 5. Data

### 5.1 The snapshot

`public/data/opportunities.json` is a copy of `backend/demo/greenhouse_snapshot.json`. It holds public Greenhouse job-board data with HTML removed. Each listing names its employer and links to the original posting, which the file's own notice calls the source of truth. Refresh it with the connector in the backend, not by hand.

Fields used by the front end:

| Field | Used for |
|---|---|
| `employer`, `title`, `department`, `location_text` | Cards, detail, and search |
| `description` | Detail page, as plain text |
| `eligible_countries` | Country filter, tags, and the launch-country count |
| `work_mode`, `scope` | Filters, tags, and labels |
| `updated_at` | Sorting, featured roles, and the date shown |
| `expires_at` | Expiry notice on the detail page |
| `source_url` | Apply link |
| `source_key`, `external_id` | Listing id and React keys |
| `pay_ranges` | Shows "See the posting" when present; otherwise "Not stated in the posting" |
| `fetched_at` (top level) | "Last refreshed" text |

Fields present but unused: `unmapped_locations`.

### 5.2 Moving to the API

When `/v1` exists:

1. Change `DATA_URL` in `src/hooks/useOpportunities.ts` to the endpoint.
2. Keep the response shape matching `OpportunitySnapshot` in `src/lib/opportunities.ts`, or change the type and the code that reads it.
3. Move filtering, sorting and paging to the server once the listing count justifies it. The current client code assumes the whole list is in memory.

### 5.3 Sectors

The listing data has no sector field, so `src/lib/sectors.ts` assigns sectors by whole-word keyword match against title and department. The four sectors are Software & Cloud, Data & Analytics, Finance & Fintech, and Logistics & Operations. The counts are approximate. Replace the matching with the sector field once the API provides one.

## 6. Labels and fixed values

These come from TECHNICAL.md §14 and DATABASE.md. Do not invent new values in the front end.

| Value | Label |
|---|---|
| `work_mode: remote` | Remote |
| `work_mode: onsite_or_hybrid` | On-site or hybrid |
| `scope: in_region` | In your region |
| `scope: remote_in_region` | Remote, in your region |
| `scope: outside_region` | Not in your country |
| `scope: remote_outside_region` | Remote, not in your country |
| `scope: unspecified` | Eligibility unclear |

`WorkMode` and `Scope` are closed unions in `src/lib/opportunities.ts`. If the backend adds a value, add it there first. The label tables are typed by those unions, so the compiler will flag a missing label.

## 7. Design system

Colours, fonts and the type scale are defined once, as Tailwind theme variables in `src/index.css`:

- **Blue is the base colour.** The page background is `blue-100`, cards and inputs are `blue-50`, and hover states use `blue-200`. White is used only for text on blue.
- **Bands:** the header, footer, sections marked as `tone="blue"`, and photo bands use `accent-blue` or `accent-navy`.
- **Text:** `ink-900` to `ink-500` on light blue; `white` and `blue-200`/`blue-100` on blue.
- **Accents:** `accent-blue` for actions and focus, `accent-navy` for primary buttons, and `accent-teal` is reserved for verified status (none is shown yet).
- **Fonts:** `font-serif` (Newsreader) for headings, `font-sans` (Plus Jakarta Sans) for body, `font-mono` for metadata.

Use these tokens instead of raw hex values. Hairline dividers and borders replace shadows.

## 8. Rules

- **Plain text only.** Listing titles and descriptions are third-party text. They are rendered as text nodes and never through `dangerouslySetInnerHTML`.
- **Links go to the source.** The app links to the employer's posting and does not claim to take applications.
- **No personal data.** The front end has no accounts, forms or profile fields. The signup flow, when built, must not ask for name, date of birth, gender, national ID, photo or school name.
- **No inline scripts or styles.** The CSP is `default-src 'self'` with `style-src 'self'` and `script-src 'self'`. Do not add inline `style` props that need `'unsafe-inline'`, inline event attributes, or external scripts or fonts. React `style` props are rendered as inline styles, so avoid them.
- **Accessibility.** Labelled form controls, a visible focus ring (`:focus-visible`), a skip link, a live region for result counts, `aria-hidden` on decorative icons, one `h1` per page, and reduced-motion rules in `index.css`.
- **Images.** Photographs are self-hosted in `public/images/` (Unsplash License, no people in frame), so the CSP's `img-src 'self'` still holds. Images are decorative (`alt=""`), so the text beside them carries the meaning.
- **Document titles.** Each page calls `useDocumentTitle`.

## 9. Commands

Run from the repository root:

```bash
pnpm install        # from pnpm-lock.yaml
pnpm dev            # http://localhost:5173
pnpm test           # vitest run, once
pnpm typecheck      # tsc -b, no emit
pnpm build          # typecheck, then vite build into dist/
pnpm preview        # http://localhost:4173, serves dist/
```

Run `pnpm typecheck && pnpm test && pnpm build` before merging frontend changes. On a machine without pnpm, use `corepack` or `npm install -g pnpm@12.15.0`. Do not use `npm install` in this repository, because `devEngines` will refuse it.

## 10. Testing

| File | Covers |
|---|---|
| `src/lib/opportunities.test.ts` | Each filter and combinations; country matching; search terms; sorting and no mutation; country list; directory stats; listing ids; expiry; sector counts |
| `src/App.test.tsx` | Landing counts, featured roles, hero search hand-off, no unverified figures; directory paging, sector from URL, search and clear, card links, error state; detail content, expired posting, not found; standards labels; draft legal notice; 404 |

Route tests use `createMemoryRouter` with the real route table and a stubbed `fetch`. The snapshot cache is cleared between tests.

**Not covered yet:** visual layout, mobile widths, real-browser behaviour, and automated accessibility checks (axe). A Playwright run is the next step.

## 11. Deployment

`infra/render.yaml` defines a Render static site, `ypp-web`:

- **Build:** installs pnpm 12.15.0, then `pnpm install --frozen-lockfile && pnpm build`.
- **Publish:** `./dist`.
- **Rewrite:** `/*` to `/index.html`, so deep links such as `/opportunities/…` load the app. Without this, a refresh on a deep link returns 404.
- **Node:** `NODE_VERSION` 22.
- **Headers:** `Content-Security-Policy`, `Strict-Transport-Security` (one year, `includeSubDomains`), `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, and a `Permissions-Policy` that disables camera, microphone and geolocation.

When the API is added, its origin must go into `connect-src`.

## 12. Decisions

| Decision | Why | Trade-off |
|---|---|---|
| Vite rather than Next.js | Client-side pages are enough for now; the README originally named Next.js | No server rendering, so listing pages will not be indexed well by search engines until that changes |
| Tailwind 4 through Vite, not the CDN | The CDN breaks the CSP and cannot be used in production | A build step is needed for styling changes |
| Self-hosted fonts | The CSP blocks external font hosts; no request leaves the site | About 400 KB of font files in total. Browsers fetch only the subsets a page uses, but the full set is shipped |
| Static snapshot | The API does not exist yet; the snapshot lets the site be deployed and reviewed | Data is only as current as the last snapshot |
| Client-side filtering and sorting | The data is small, and the logic is pure and tested | Must move to the server once listings are paged by the API |
| URL-driven filter state | Shareable links and working back button without a state library | Filter values are validated on read, so bad URLs fall back to defaults |
| Sectors from keywords | No sector field exists yet | Approximate counts; replace once the data has sectors |
| No UI kit | Keeps the bundle small and the design exact | More hand-written markup |
| pnpm with the version pinned | Reproducible installs | Contributors need pnpm 12 |

## 13. Known limits

- The data is a static snapshot. It does not update on its own.
- Dead employer links are not detected.
- Sectors are approximate.
- The landing page's "How it works" describes what exists today. It does not describe matching, which is not built.
- The legal pages are drafts with placeholders that must be filled in.
- Not tested in a real browser, on phones, or with a screen reader.

## 14. Next steps

1. Replace the snapshot with the `/v1` listings endpoint, and move filtering and paging to the server.
2. Add a Playwright run for the main flows and a mobile viewport, and an axe check on each page.
3. Build sign-in, onboarding and the signed-in pages once authentication exists (DESIGN.md §7, steps 3 and 4).
4. Trim the font files to the subsets the site needs.
5. Add the web service to `infra/render.yaml` alongside the API when the backend can be deployed.
