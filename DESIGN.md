# NextStep: Page Design

This document designs the pages of **NextStep**, the web product for the Youth Yellow Pages directory. It covers the visual system, the sitemap, and a specification for each page: purpose, layout, data source, states, and whether the backend supports it today. It does not build any pages. For the front-end architecture see [docs/FRONTEND.md](docs/FRONTEND.md). For the backend see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/TECHNICAL.md](docs/TECHNICAL.md).

> **Naming.** The product is called NextStep. The landing-page sample and the repository docs still say "Youth Yellow Pages", which is the name of the directory service. This document uses NextStep as the product name and keeps "Youth Yellow Pages" for the directory engine and the repository. Confirm the brand before the name appears in the live site, the footer, or the legal pages.

## 1. Design direction

NextStep should read like a careful editorial publication, not a job-board marketplace. Young people are the audience, so the tone is calm and direct, with no urgency tricks and no hype. Every claim on the page must be backed by evidence the product can show.

Four principles follow from the product rules in the README and TECHNICAL.md:

1. **Evidence before identity.** Skills and proof are shown first. Names, photos, and school names are never part of a ranking or a first impression.
2. **Explain every score.** Any match percentage links to its breakdown and the gaps behind it.
3. **Source of truth is the employer.** Every listing shows its origin and links to the original posting.
4. **Plain text and honest numbers.** Only verified figures appear, and each one shows how it was measured.

## 2. Visual system

The sample landing page sets the base. It is written with the Tailwind CDN, so the tokens below need to move into the React app before launch (section 8).

### 2.1 Colour

| Token | Hex | Use |
|---|---|---|
| `cream-50` | `#FAF8F5` | Page background |
| `cream-100` | `#F6F2EA` | Cards, input fill, subtle panels |
| `cream-200` | `#EDE5D6` | Hover on pills |
| `cream-300` | `#DFD4BE` | Reserved for dividers on warm surfaces |
| `ink-900` | `#0E1726` | Primary text, primary buttons |
| `ink-800` | `#14213D` | Body text (`body` colour) |
| `ink-700` | `#1F2E4D` | Secondary button text, pill text |
| `ink-600` | `#344363` | Supporting text |
| `ink-400` | `#64748B` | Meta text, numbers, placeholders |
| `ink-300` | `#94A3B8` | Separators |
| `accent-blue` | `#0F4C9A` | Links, focus accents, primary actions |
| `accent-navy` | `#002B66` | Hover on blue actions |
| `accent-teal` | `#1B7A68` | Verified status only |
| Amber `600` | Tailwind default | Single star in the header status pill |

Rules: teal means "verified" and nothing else. Blue means "action". Amber is reserved for the rating mark.

**Gap to fix.** The sample uses `text-ink-500` in several places, but the Tailwind config defines no `ink-500`, so those elements silently fall back to inherited colour. Define `ink-500` (suggested `#4B5C78`, between `ink-400` and `ink-600`) or switch those uses to `ink-400`/`ink-600`. The sample also references `bg-chip-blue-soft` in `selection:` classes, which is also undefined. Define it as `#E3ECFA` (the value already used in the custom `::selection` rule).

### 2.2 Type

| Role | Family | Use |
|---|---|---|
| Display | Newsreader (serif), 300–600 with italic | Headlines, card titles, section headings, the wordmark |
| Body | Plus Jakarta Sans, 300–700 | Paragraphs, buttons, form fields |
| Metadata | `ui-monospace` stack | Numbers, counts, labels, timestamps, section indices |

Scale used on the landing page, reused across the product:

- Display: 48 / 60 / 72 px (mobile, tablet, desktop), line-height 1.08, tracking −0.03em
- Section heading: 30 / 36 px, serif
- Card title: 24 / 30 px serif (featured roles), 16 px sans semibold (small cards)
- Body: 14–20 px sans; long reading (detail pages) at 16–18 px with line-height 1.6
- Meta: 11–13 px mono, uppercase only for short labels

Use `font-feature-settings` as set in the sample. Load fonts from the app's own origin (section 8).

### 2.3 Layout and components

- **Container:** `max-w-7xl` (1280 px) with horizontal padding of 24 px on mobile and 48 px on large screens.
- **Hairline dividers** (`ink-900/10`) separate sections. Do not use shadows for structure.
- **Numbered sections** (`01`–`05`) in mono give the page an index. Use them only on the landing page and the About page.
- **Cards:** 16 px radius, 1 px `ink-900/8` border, hover lifts to white with a `ink-900/20` border. No drop shadows.
- **Pills:** fully rounded, `cream-100` fill, 1 px border. Used for filters and tags.
- **Buttons:** primary is `ink-900` (hover `accent-blue`), or `accent-blue` for the main action in a search. Secondary is ghost. Minimum target 44 px high on touch.
- **Verified badge:** a teal dot plus "Verified Employer" text. Never an icon alone.
- **Match score:** always shown as a percentage with its band word ("strong", "partial", "early") and a "why" link. Never a bare number.

### 2.4 Motion

Transitions are 150–200 ms on colour, border and transform. Hover translation is 2 px on arrows only. Respect `prefers-reduced-motion` by removing transforms and transitions. No scroll-jacking. `scroll-smooth` on the root is acceptable because the page has in-page anchors.

### 2.5 Accessibility baseline

- Contrast: body text `ink-800` on `cream-50` is well above 4.5:1. Meta text `ink-400` on `cream-50` is about 4.1:1 and fails for small text. Use `ink-600` for any text under 14 px, or darken `ink-400` for body-size meta.
- Every interactive element has a visible focus ring. The sample uses `focus-within` on the search field, which is good; add `focus-visible` rings on pills and cards too.
- Icons from Material Symbols are decorative and need `aria-hidden="true"`. Icon-only buttons need an `aria-label`.
- Forms have real `<label>` elements. Placeholders are hints, not labels.
- The page has one `h1`. Section headings are `h2`, card titles are `h3`.

## 3. Sitemap

```
/                          Landing (NextStep home)
/opportunities             Directory: browse and filter listings
/opportunities/:id         Opportunity detail and match preview
/standards                 Verified Employer Seal, paid guarantee, fair-work rules
/about                     Mission, numbers, method, team
/signin  /signup           Accounts (choose youth or employer)
/onboarding                Build a profile (youth), step by step
/me                        My profile, evidence, and matches
/me/matches/:listingId     My skill gap for one listing
/me/privacy                Consent, visibility, export, and deletion
/employers                 Employer dashboard
/employers/listings/new    Post a listing
/employers/talent          Talent search for a listing (blind-first)
/employers/talent/:profileId  Candidate view (evidence first)
/privacy  /terms  /accessibility  Legal
/404  /500  /offline       Error and maintenance states
```

Public pages: `/`, `/opportunities`, `/opportunities/:id`, `/standards`, `/about`, the legal pages, and the error pages. Everything under `/me` needs a youth account. Everything under `/employers` needs an employer account. The server enforces both. The front end only hides links.

## 4. Page specifications

Each page lists: **Who** it serves, **Goal**, **Layout**, **Data**, **States**, and **Status** against the current backend.

Status values:
- **Ready:** the backend already supports the data. Only the REST layer or the UI is missing.
- **Needs REST:** the data exists in the service layer but has no public REST route yet.
- **Blocked:** the feature is not built. The page can be designed but not wired.

### 4.1 Landing (`/`)

**Who:** a young person arriving from a search, a link, or a campus poster.
**Goal:** understand what NextStep is in one screen and start a search or sign-up.

**Layout (from the sample, with corrections):**

1. **Header:** wordmark, four numbered anchor links, a status pill, and an "Explore directory" button. The status pill currently shows "94.6% Verified Match · 1,420 Placements". See section 6 for why these figures need checking before they stay.
2. **Hero:** category line, headline ("Find your first step into work."), subtext, a search field, three filter pills, and a count line.
3. **01 Sectors:** four cards with a role count each. Each card links to `/opportunities` with the sector pre-filled.
4. **02 Featured roles:** three large cards. Each shows employer, location and work mode, verified badge, title, one-line description, pay, match preview, and "View details".
5. **03 The Standard:** three steps (build profile, see match reasons, blind review).
6. **04 By the numbers:** four figures.
7. **05 Get started:** email capture and a primary CTA.
8. **Footer:** wordmark, four columns, copyright, and legal links.

**Layout notes for the build:**

- The hero search should submit to `/opportunities?q=…`. The sample's `onsubmit` inline handler is blocked by the Content-Security-Policy in `infra/render.yaml`, so this must be a React form handler.
- The three filter pills should set filters on the directory, not run a separate search.
- The featured roles should come from the listings data with a rule for choosing them (for example, the most recently verified, not hand-picked). Show a real count of listings and never the sample's invented employers.
- The "Browse all" link goes to `/opportunities`.
- Section 05 email capture needs a consent line that says what the email is used for. Store it only after the user confirms.

**Data:** sector counts and listing count need the listings endpoint (Needs REST). Featured roles need the same. Figures in section 04 and the header need a source (section 6).

**States:** while loading, show the static hero and skeleton cards. If listings fail, hide the featured section and keep the rest of the page. Never show an error on the landing page.

**Status:** Ready for layout. Needs REST for live counts and featured roles.

### 4.2 Directory (`/opportunities`)

**Who:** anyone, signed in or not.
**Goal:** find listings that could fit, and see where each one is open to them.

**Layout:**

```
┌──────────────────────────────────────────────────────────────┐
│ Header                                                       │
├──────────────────────────────────────────────────────────────┤
│ Search [ ........................................ ] [Search] │
│ Country ▾   Work mode ▾   Eligibility ▾   Sector ▾   Clear   │
├──────────────────────────────────────────────────────────────┤
│ 272 opportunities · Listings last refreshed 23 Oct 2026      │
│ Sort: Most recent ▾                                          │
│ ┌─────────────────────┐ ┌─────────────────────┐              │
│ │ Employer            │ │ Employer            │              │
│ │ Title               │ │ Title               │              │
│ │ tags: work · scope  │ │ tags                │              │
│ │ location · updated  │ │                     │              │
│ │ [View] ↗ source     │ │ [View] ↗ source     │              │
│ └─────────────────────┘ └─────────────────────┘              │
│                    [ Show more ]                             │
└──────────────────────────────────────────────────────────────┘
```

**Differences from the current build:**

- Adds a **Sector** filter (the sample's four tracks) and a sort control.
- Cards use the NextStep card style and add a "View" link to the detail page. The "View original posting" link stays as a secondary action.
- Eligibility labels follow docs/TECHNICAL.md §14 (and docs/FRONTEND.md §6) and must match the wording in section 5.
- Filters stay in the URL (`?country=KE&scope=in_region`) so a search can be shared and the back button works.

**Data:** Needs REST. The existing `GET`-style listing data in `public/data/opportunities.json` is the stand-in. `search_opportunities` is the MCP tool for this, but it needs a `profile_id`, so it is for signed-in youth only. The public directory needs its own endpoint that does not require an account.

**States:** loading (skeleton cards), empty ("No opportunities match these filters. Try clearing some of them." plus a Clear button), error (message and retry), and end of list.

**Status:** Needs REST.

### 4.3 Opportunity detail (`/opportunities/:id`)

**Who:** a youth deciding whether to apply, or an employer checking how their listing reads.
**Goal:** understand the role, see how it matches the viewer's profile, and apply through the employer's own posting.

**Layout (single column, 680 px reading width, with a side panel on large screens):**

1. Breadcrumb: Directory › Sector › Title.
2. Header: employer with verified badge, title, location, work mode, pay (only when stated), updated date, and expiry date when set.
3. **Match panel** (signed-in youth only): score as a percentage with band word, "Why" disclosure with the breakdown from `get_skill_gap`, and the missing skills with the projects that would close each one.
4. Description: plain text, with paragraphs preserved. No HTML rendering.
5. Eligibility: country and scope in plain words ("Open to people in Kenya", "Remote, names Kenya", "Eligibility unclear: check the employer's posting").
6. Primary action: "Apply on the employer's site" (opens `source_url` in a new tab). Secondary: "Save" (later).
7. Footer note: the source of truth is the employer's posting, and NextStep does not hold applications.

**Data:** the listing needs Needs REST. The match panel needs `get_skill_gap(listing_id, profile_id)`, which is ready in the service layer but only over MCP and only for a signed-in user's own profile.

**States:** listing not found (404 page with a link back to the directory), listing expired (show the notice and hide the apply button), no profile yet (show "Build your profile to see your match" instead of a score).

**Status:** Needs REST for listing data. Match panel: Ready in the service, needs REST or an authenticated front-end client.

### 4.4 Standards (`/standards`)

**Who:** employers, careers offices, and youth asking "can I trust this?"
**Goal:** explain how a listing gets verified and what the platform promises, in writing.

**Layout:** a long-form page in the serif body style. Sections: how an employer becomes verified (the Verified Employer Seal), the paid guarantee, the fair-work rules, how scores are calculated (with a link to the scoring model), and how personal data is handled.

**Content rule:** every guarantee on this page must match a contract or policy. The sample's "100% paid guarantee" cannot be published until the terms are written and reviewed (section 6).

**Data:** none. Static content.

**Status:** Ready to design. The policy text depends on counsel.

### 4.5 About (`/about`)

**Who:** funders, partners, and the press.
**Goal:** state the mission and the method, and show measured results.

**Layout:** a short statement, the four numbers from the landing page with a "how measured" note under each, the method in three steps, and a team and partners section. Use the numbered section style.

**Data:** the figures need a source. Until the outcome tracking (`record_outcome`) exists, the page must not show placement counts.

**Status:** Blocked for figures (outcome tracking not built). Layout Ready.

### 4.6 Sign in and sign up (`/signin`, `/signup`)

**Who:** youth and employers.
**Goal:** get into the right account type with the least friction.

**Layout:** a single centred card on `cream-50`. Step one: "I am a young person" or "I am an employer" as two large choices. Step two: email, and the sign-in method. For youth, the signup form asks only for what is needed to create the account (email, country). It does not ask for name, date of birth, gender, or school. Those fields must not exist in the signup flow, because the platform does not use them for scoring.

**Copy:** a line below the form says what the account is for and links to the privacy page.

**Data:** authentication is not built. The architecture sets the approach (docs/ARCHITECTURE.md §7, Authentication), but the provider and the web sign-in flow are still open. Design the screens, but do not wire them until the auth decision is made.

**States:** invalid email, email already in use (say so without revealing other account details), rate limit reached, and a "check your email" confirmation step.

**Status:** Blocked (authentication not decided or built).

### 4.7 Onboarding: build your profile (`/onboarding`)

**Who:** a youth account holder who has just signed up.
**Goal:** create a profile with enough real evidence to be matched, in under ten minutes, and see that it is useful at each step.

**Steps (one question per screen, with progress shown):**

1. **Where you are:** country (NG, ZA, KE or GH), and whether you are open to remote roles.
2. **What you can do:** search the skills taxonomy (`list_skills`), add skills, and set a level for each. Show how many listings each skill appears in.
3. **Your proof:** add evidence links (a GitHub repository, a coursework project, a certificate upload). Each piece of evidence shows whether it is pending verification.
4. **What you are looking for:** role type (attachment, internship, entry-level), and the earliest start date.
5. **Visibility and consent:** choose which fields are public. Show the default (blind: skills and evidence only). Explain what the employer sees.
6. **Review:** a preview of the profile as an employer will see it, and a button to publish.

**Rules:**

- Skill levels are self-rated and marked as such until evidence confirms them.
- Uploads go to object storage, and the form only stores the reference.
- Autosave on every step. The user can leave and come back.
- Never ask for a national ID, gender, age, photo, or school name. Keep the copy free of any "upload a photo" prompt.

**Data:** reading the taxonomy is ready in the service (`list_skills`). Writing the profile, evidence, and consent has no write tool yet (Blocked).

**Status:** Blocked for saving. The screens can be designed and tested with fixtures.

### 4.8 My profile and matches (`/me`)

**Who:** a signed-in youth.
**Goal:** see the state of their profile, see where they match, and know what to do next.

**Layout:**

- **Top:** name for display only (the user's own view), country, profile completeness, and "Edit profile".
- **Matches:** listings open to the user, ranked by score, with the band word and the single biggest gap for each. Toggle to include listings outside their country, labelled "Not in your country", as the MCP tool offers.
- **Evidence:** list of proof items with verification state.
- **Next step:** one card suggesting the project that closes the largest gap, with the time it takes.

**Data:** `search_opportunities(profile_id, include_global, min_score, limit, cursor)` gives the matches. `get_profile` gives the public view. Both are Ready in the service and need an authenticated REST route.

**States:** no matches yet (explain why and suggest the next step), profile incomplete (show the missing step, not a blank page).

**Status:** Needs REST and auth.

### 4.9 My skill gap (`/me/matches/:listingId`)

**Who:** a youth looking at one listing.
**Goal:** see exactly what is missing and what to build to close it.

**Layout:** the score at the top with its band. Below, a table of required skills (must-have and nice-to-have) with the user's level and the gap. Each gap has the project that closes it and an estimated effort. A "Why this score" section lists the components of the score in plain words.

**Writing rule:** the text describing gaps is generated from structured data, not free text. If explanation text is generated by the model, it is shown as "generated explanation" and labelled as such.

**Data:** `get_skill_gap(listing_id, profile_id)`.

**Status:** Ready in the service. Needs REST and auth.

### 4.10 Privacy and my data (`/me/privacy`)

**Who:** a youth account holder.
**Goal:** control what is visible and what is kept.

**Layout:** three blocks.

1. **Visibility:** a list of profile fields with a toggle each. The default is the blind set.
2. **Consent history:** what the user agreed to and when, with a withdraw action for each.
3. **Export and delete:** download my data, and delete my account. Deletion is a soft delete with a 30-day purge window, as stated in docs/ARCHITECTURE.md §7. Say so on the page.

**Rules:** deletion needs a confirmation step that names the consequences. No dark patterns: the "delete" action is not styled as the primary action and is not hidden in a menu.

**Data:** consent and deletion have no tool or route yet (Blocked).

**Status:** Blocked.

### 4.11 Employer dashboard (`/employers`)

**Who:** a verified employer or their recruiter.
**Goal:** see open listings, the state of each, and the candidates who match them.

**Layout:** a list of the employer's listings with status (draft, open, expired), candidate count, and the date of the last match run. A primary action: "Post a listing". A secondary panel: outcomes recorded for past hires, which feeds the platform's success measure.

**Data:** listing management and outcome recording have no tool yet (Blocked: `create_listing` and `record_outcome` are the write tools named in the README).

**Status:** Blocked.

### 4.12 Post a listing (`/employers/listings/new`)

**Who:** an employer.
**Goal:** publish a listing that is clear, accurate, and eligible for matching.

**Layout:** a four-step form: role (title, sector, description), place (location text, countries it is open to, work mode), terms (pay range if any, start date, duration, expiry), and review. The form shows the eligibility label the listing will get, before it is published.

**Rules:**

- Pay is optional. A listing without pay shows "pay not stated". Never imply pay where none is given.
- The employer's own posting URL is required, because it is the source of truth.
- Show how the country and work mode will be read, so the employer can correct them.

**Data:** `create_listing` (Blocked).

**Status:** Blocked. Design now.

### 4.13 Talent search (`/employers/talent`)

**Who:** a verified employer with an open listing.
**Goal:** find candidates who match the requirement, while judging skills before identity.

**Layout:**

- Left: the requirement (skills must-have and nice-to-have, country, minimum score), taken from a listing or built here.
- Right: ranked candidates. Each row shows a score with band, the top three matched skills with evidence counts, the largest gap, and "View evidence". No name, photo, or school in the row.
- Toggle: "Blind review" is on by default. Turning it off is not offered until a candidate has passed the technical criteria, which matches the product promise.

**Data:** `search_talent(query, country, skills, min_score, limit, cursor, rerank)`. Ready in the service; needs REST and employer auth.

**States:** no candidates (suggest loosening a requirement, with the effect on the count), requirement too narrow, and pagination.

**Status:** Needs REST and auth.

### 4.14 Candidate view (`/employers/talent/:profileId`)

**Who:** an employer reviewing one candidate.
**Goal:** judge the evidence.

**Layout, in this order:** the score and its breakdown, the evidence items (each with its source and verification state), the skills with levels and gaps, and the candidate's own summary text. Identity fields appear last, behind a separate "Reveal details" action that is enabled only after the technical criteria are passed.

**Rules:**

- Candidate text is user-authored and shown as plain text in a clearly marked block.
- No action on this page changes the candidate's data.
- The page logs each profile view for the audit trail, as the service does.

**Data:** `get_profile`, `score_candidate`. Needs REST and auth.

**Status:** Needs REST and auth. The reveal step is Blocked until the review workflow exists.

### 4.15 Legal: privacy, terms, accessibility (`/privacy`, `/terms`, `/accessibility`)

**Who:** everyone.
**Goal:** say what is collected, why, how long it is kept, and how to ask questions. The privacy page must match DATABASE.md retention and the consent model.

**Layout:** a plain long-form page with a table of contents, a "last updated" date, and a contact address. The accessibility page lists the standard targeted, known gaps, and how to report a barrier.

**Status:** Designed; text needs counsel review (section 6).

### 4.16 Error and status pages

- **404:** short message, search box that goes to the directory, and two links (Directory, Home).
- **500:** short message, the time, and a retry button. Do not show stack traces or request IDs to users; log them.
- **Offline:** shows the last loaded directory if cached, with a banner saying so.
- **Maintenance:** a single message with the expected return time when known.

**Status:** Ready to design and build without the backend.

## 5. Shared rules

**Eligibility labels.** Use these exact phrases on every page. They come from TECHNICAL.md §14.

| Scope | Label | Shown to |
|---|---|---|
| `in_region` | In your region | Everyone |
| `remote_in_region` | Remote, in your region | Everyone |
| `outside_region` | Not in your country | Labelled, shown in global view only |
| `remote_outside_region` | Remote, not in your country | Labelled, shown in global view only |
| `unspecified` | Eligibility unclear | Labelled |

**Scores.** Show the percentage with its band word. The band names come from the scoring model in TECHNICAL.md §6. A score alone is never shown.

**Dates.** Day, month, and year in the user's locale, with the time zone when it matters (expiry). Use the format `23 Oct 2026` on cards.

**Currency.** Show the currency code from the listing (`KES`, `ZAR`, `NGN`, `GHS`). Never convert.

**Empty and error copy.** Say what happened and what to do next. Avoid "Oops".

**Personal data.** No page asks for a name, date of birth, gender, national ID, photo, or school name in a form that feeds scoring. Display names are the user's own choice and are not used in ranking.

## 6. Content to verify before launch

The sample page makes claims and shows figures. Each one needs a source or must be removed. The product's success measure is verified paid placements and six-month retention (README), so placement claims must come from `record_outcome` data.

| On the sample | Problem | Action |
|---|---|---|
| "94.6% Verified Match" and "Transparent match accuracy 94.6%" | A match rate and an accuracy rate are different measures. The figure has no stated method | Define both measures and publish the method, or remove |
| "1,420 placements" / "Students placed this year" | No outcome data exists yet | Use only confirmed outcomes, with the period stated |
| "100% paid guarantee on every role" | A commercial and legal promise | Publish only if the policy exists and is reviewed; otherwise remove |
| "48 hrs average employer response time" | No measurement exists | Remove until measured |
| "520+ verified roles · 128 vetted employers" | The directory holds 272 snapshot listings; the verified count is not defined | Use the live count with its definition of "verified" |
| "Live in Nairobi & remote" / "across Kenya" | The product covers Nigeria, South Africa, Kenya and Ghana | Name all four countries, or label the launch scope |
| Featured roles: Acme Fintech, Twiga Logistics, Kenya Cloud Systems | Placeholder names. Real employers must be real and verified | Replace with live listings; never ship placeholders |
| "NITA Verification Sync" in the footer | Names a specific integration that may not exist | Confirm, or remove |
| "© 2025" | The year is 2026 | Use the current year in the footer |
| "Verified Employer Seal" and "Verified" tags | A verification process must exist behind the label | Define the process on `/standards` first |

## 7. Build order

Pages that need no backend first, so they can be reviewed and tested early:

1. Landing (static content and layout), error pages, legal pages, and `/standards`.
2. Directory and detail, using the static snapshot as the data source.
3. Sign-in and onboarding screens, with fixtures and no saving.
4. Signed-in pages (`/me`, skill gap, privacy), once REST routes and auth exist.
5. Employer pages (dashboard, posting, talent search, candidate view), once the write tools and employer auth exist.

## 8. Implementation notes for the React app

- **Move tokens into the app.** Replace the Tailwind CDN script with the Tailwind build through Vite, and put the colours, fonts, and spacing from section 2 into the theme. The CDN cannot be used in production: it loads script from outside the origin, and the CSP in `infra/render.yaml` (`script-src 'self'`) blocks it.
- **Self-host fonts.** Google Fonts stylesheets are blocked by `style-src 'self'` and `font-src`. Download the Newsreader, Plus Jakarta Sans, and Material Symbols files into `public/fonts`, and load them with `@font-face`.
- **No inline handlers.** The sample's `onsubmit="event.preventDefault();"` must become React `onSubmit` handlers. Inline event attributes are blocked by the CSP.
- **Routing.** Add a client-side router (for example React Router) for the sitemap in section 3. Add a rewrite to `index.html` in `infra/render.yaml` so deep links work on Render.
- **Components to build once:** `Header`, `Footer`, `Section` (with numbered index), `Card`, `Pill`, `Button`, `VerifiedBadge`, `ScoreBadge`, `EligibilityTag`, `Hairline`, `FilterBar` (exists), `OpportunityCard` (exists, to be restyled).
- **Data layer.** Keep the `lib/` pattern from docs/FRONTEND.md: pure functions for formatting and filtering, and a thin fetch layer that the API replaces.
- **Testing.** Each page gets one render test and one accessibility check (axe). The sample's colour pairs need a contrast check before sign-off.

## 9. Open decisions

1. **Brand:** NextStep or Youth Yellow Pages as the public name. Confirm before launch.
2. **Launch countries:** all four, or Kenya first. The sample says Kenya; the product scope says four.
3. **Authentication:** the method and provider. Blocks sign-in, onboarding, and every signed-in page.
4. **Public listings endpoint:** the directory and landing page need listings without an account. This is a new REST route, separate from the personalised MCP tool.
5. **Verification process:** what makes an employer "verified", and who checks it. Blocks the seal and the verified tags.
6. **Guarantee and figures:** the paid guarantee and any published statistics, which need counsel and measured data (section 6).
7. **Tailwind and fonts:** confirm the move to a built Tailwind setup and self-hosted fonts (section 8).
