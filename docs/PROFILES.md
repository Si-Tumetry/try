# Profiles, CV scoring and the matches dashboard

This document covers the first working version of the member profile: a CV is uploaded, the skills in it are recognised, and every listing is scored against them on the dashboard. For the scoring model see [TECHNICAL.md](TECHNICAL.md) §6. For the product design see [../DESIGN.md](../DESIGN.md), sections 4.7 to 4.9.

## 1. What a member does

1. Opens `/profile` and uploads a CV (PDF, Word `.docx`, plain text or Markdown, up to 5 MB).
2. Chooses the country they live in, when they can start, and whether employers may find their skills. Employer search is off by default.
3. Agrees that NextStep reads the skills in the CV to score them against listings. This box is required.
4. Sees the skills recognised in the CV, then opens `/dashboard`.
5. On the dashboard, each listing open in their country shows a score out of 100, a band, the skills they match, the skills to add, and a suggested next project.

Members can replace the CV or change their details on `/profile`, and can delete their profile, which removes their skills and their matches.

## 2. How a CV becomes a profile

| Step | Module | What happens |
|---|---|---|
| Read the file | `backend/core/cv/extract.py` | Checks the size and the file type, and checks that the file starts with the right signature (`%PDF` or a zip header). Reads text from PDF (`pypdf`), Word (the XML inside the zip) or plain text. Rejects files with too little text, such as scanned images. |
| Find skills | `backend/core/cv/skills.py` | Matches the 303 names and aliases in `backend/taxonomy/skills.json` against the text, as whole phrases. Counts mentions. |
| Set levels | `backend/core/cv/skills.py` | A skill named once is recorded at level 2. A skill named two or more times is recorded at level 3. These match the default levels for requirements, so repeated mentions meet a must-have. |
| Save | `backend/core/services/profiles.py` | Stores the country, availability, the searchable flag and the skills. **The CV text and the file are not saved.** |

Skills are self-declared, because nothing confirms them yet. Self-declared evidence carries low weight in the score (`SELF_DECLARED_WEIGHT` in `core/scoring.py`).

A CV with no recognised skills is rejected with a message that asks the member to add their tools and practical skills.

## 3. Endpoints

All responses are JSON. Errors use `{"error": {"code": ..., "message": ...}}`.

| Method and path | Auth | Purpose | Success |
|---|---|---|---|
| `POST /v1/profiles` | none | Create a profile from a CV. Multipart fields: `cv` (file), `country`, `consent` (`true`), `availability`, `searchable`. | `201` with `{"token", "profile"}`. The token is shown once. |
| `GET /v1/me/profile` | bearer | Read the profile. | `200` with `{"profile"}` |
| `PUT /v1/me/profile` | bearer | Update country, availability and visibility. Send `cv` to replace the skills. | `200` with `{"profile"}` |
| `DELETE /v1/me/profile` | bearer | Delete the profile and revoke the token. | `204` |
| `GET /v1/me/matches` | bearer | Score every listing open in the member's country. Query: `limit` (1 to 50, default 20), `min_score` (0 to 100), `cursor`. | `200` with `{"results", "total_matching", "next_cursor"}`, highest score first |
| `GET /v1/me/matches/{listing_id}` | bearer | The skill gap for one listing, with suggested projects. | `200` |
| `GET /v1/health` | none | Liveness check. | `200` |

Each result in `results` contains `listing_id`, `title`, `employer`, `location`, `scope`, `in_your_country`, `source_url`, `score`, `band` (`strong`, `good`, `partial` or `weak`), `confidence` (`high`, `medium` or `low`), `matched_skills`, `missing_skills`, and `next_project`.

The dashboard asks for `min_score=0`, so every job appears with its score. The service's own default is 40, which is the product rule for search.

## 4. Sessions

There are no accounts yet. Creating a profile issues a random bearer token, which the server keeps only as a SHA-256 digest (`backend/api/auth.py`). The browser keeps the token in `localStorage` under `nextstep.profileToken`.

This is a stand-in until sign-in is built (DESIGN.md §4.6). It has these limits:

- Clearing site data, or using another browser or device, loses the profile. There is no way to recover it.
- Tokens are held in memory, so a server restart ends every session. Profiles are lost too, because the store is in memory.
- Tokens do not expire, and there is no rate limit on creation.

Do not put this in front of real members until accounts and Postgres storage exist. The `SessionTokens` class is the piece to replace.

## 5. Privacy rules applied

- The CV file and its text are not stored. Only the country, availability, the searchable flag and the skill list are kept.
- Names, contact details and photos are not used for scoring, and the profile API never returns them.
- Employers see a profile only when the member has turned on "Let employers find my skills". Their search results contain skills and levels. A test checks that no contact details appear in them, and the profile never stores a name.
- Audit records hold the operation, the outcome and a hash of the arguments. They do not hold the CV, the file name or the skill list.
- Deleting the profile clears the skills and the searchable flag at once, and marks the record as deleted. Hard deletion follows the retention rules in DATABASE.md.

## 6. Scores are provisional

The score has five parts (TECHNICAL.md §6): semantic similarity, skill coverage, evidence, freshness, and fit. The semantic part needs an embedding model. **No embedding adapter is built yet**, so it is always 0 in this version.

Without it, and with self-declared skills, the highest score a job can reach is around 40. Most jobs therefore show as **weak**. The order of jobs still reflects which skills match best, and the dashboard says so.

The fix is to build the embedding adapter (`EMBEDDING_PROVIDER` in `core/settings.py`). Changing the weights or the bands needs a versioned update to TECHNICAL.md and the scoring regression suite, so this document does not change them.

## 7. Running it

```bash
# Backend (from backend/, with the venv active)
pip install -r requirements.txt
uvicorn api.asgi:app --host 127.0.0.1 --port 8000

# Frontend (from the repository root). Vite proxies /v1 to port 8000.
pnpm dev
```

The API loads the demo snapshot at start-up. `APP_ENV` must be `dev` or `demo`. Any other value stops the start, because the production store is not built.

## 8. Tests

| File | Covers |
|---|---|
| `backend/tests/test_cv.py` | Reading plain text and Word files; rejecting empty, oversized, mistyped and unreadable files; levels for repeated mentions |
| `backend/tests/test_profiles_api.py` | Creation and its rules; token checks; updates; replacing a CV; scores sorted highest first; `min_score` and `limit`; skill gap; deletion and token revocation; separation between members; employer search respects the searchable flag and shows no contact details |
| `src/pages/ProfileDashboard.test.tsx` | The dashboard with and without a token; order, scores and gaps; the score filter sends the right query; an expired token ends the session; the empty state; creating a profile; a rejected CV shows the server's message |

PDF extraction has no automated test yet, because the test suite does not include a sample PDF. Check it by hand with a real CV before release.

## 9. Known limits

- Sessions and storage are in memory (section 4).
- Scores are provisional (section 6).
- Skill detection is a dictionary match. It finds only the 303 skills in the taxonomy and their listed aliases, and it cannot tell a skill used once in a job from a skill never used. Scanned or image-only PDFs are rejected.
- Level 2 or 3 is set by how often a skill is named, which is a rough guide to depth.
- There is no review step for skills, and no evidence is attached to them yet.
- The production CSP allows only `'self'` for connections. When the API is deployed, it must be served from the same origin, or the CSP must name its origin.
- Duplicate listings from the demo snapshot appear more than once in the results.
