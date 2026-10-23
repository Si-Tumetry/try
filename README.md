# Youth Yellow Pages

A verified talent and opportunity directory for young people, small businesses, employers and opportunities across **Nigeria, South Africa, Kenya and Ghana**.

The platform has one search and scoring engine that is reachable through three doors:

- a web app (React, in this folder) and a mobile app (Flutter, built later),
- a REST API under `/v1`,
- an MCP server at `/mcp` so AI agents can query the directory through typed tools.

Ranking uses retrieval-augmented generation (RAG) and a documented skill-scoring model. Every score comes with a breakdown and evidence links, so employers see why a candidate ranked where they did.

Success is measured by **verified paid placements and six-month retention**, not by listings or sign-ups.

## Status

Built so far:

- Scoring model, RAG engine (hard filters, hybrid candidate generation with RRF, scoring, grounded LLM rerank), and the service layer.
- MCP server with the six read tools and bearer-token authentication.
- Opportunity ingestion: a Greenhouse Job Board connector, a location parser that gives each listing its eligible countries and scope, and a demo loader that refuses to run in production.
- Youth opportunity search defaults to listings open in the youth's country. A global view is available and labelled.
- 208 tests, all passing without network access, a database or AWS credentials.

Also built: cursor pagination on search and list endpoints, a settings module that reads and validates environment variables (`backend/.env.example` lists them), and deterministic skill matching for listings.

Not built yet: the Django project, REST routes, the Postgres store and migrations, Celery workers, the write tools (`create_listing`, `record_outcome`), real Bedrock adapters (including the LLM step of listing skill extraction), OAuth, the full skills taxonomy (about 300 skills; the demo uses a small test set), and the scheduled connector. The engine runs against an in-memory store until the Postgres store exists.

Refreshing the demo snapshot from the live Greenhouse boards:

```bash
cd backend
YPP_INGEST_CONTACT="you@yourdomain.org" python -m demo.refresh_greenhouse_snapshot
```

| Document | Purpose |
|---|---|
| [README.md](README.md) | Overview, repository layout, local setup, configuration |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, components, deployment on Render, request flows, decisions |
| [TECHNICAL.md](TECHNICAL.md) | Implementation detail: services, ingestion and RAG pipelines, scoring, workers |
| [DATABASE.md](DATABASE.md) | Schema, indexes, constraints, retention, migrations |
| [docs/FRONTEND.md](docs/FRONTEND.md) | React web app: structure, data, filters, testing, deployment |
| [DESIGN.md](DESIGN.md) | NextStep page designs: visual system, sitemap, and page specifications |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Symptom-first diagnostics and fixes |

The source specification is `Youth_Yellow_Pages_Technical_Design.pdf` (version 1 draft). Where these documents go beyond it, the difference is marked as an addition.

## Technology stack

| Concern | Choice |
|---|---|
| Language | Python 3.12 |
| Web framework | Django 5.2 LTS with Django REST Framework |
| MCP server | Python MCP SDK (`mcp`, FastMCP), streamable HTTP |
| Database | PostgreSQL 16 on Render, with `pgvector` and `pg_trgm` |
| Cache and broker | Redis-compatible Render Key Value |
| Background jobs | Celery 5 with Celery Beat for schedules |
| Object storage | S3-compatible bucket for CVs, certificates and uploads |
| Models | AWS Bedrock: an embedding model (Titan Text Embeddings v2, 1024 dimensions) and an LLM for extraction and explanation |
| Web front end | React 19, TypeScript, Vite, pnpm (at the repository root) |
| Hosting | Render (web, worker, beat, Postgres, Key Value) |

## Repository layout

The layout below is the target structure. Directories are created as the backend is built.

```
.
├── README.md
├── ARCHITECTURE.md
├── TECHNICAL.md
├── DATABASE.md
├── TROUBLESHOOTING.md
├── Youth_Yellow_Pages_Technical_Design.pdf
├── LICENSE
├── package.json             React web app (pnpm), Vite config, tsconfig
├── index.html
├── src/                     React components, data logic and tests
├── public/                  Static assets; public/data holds the opportunities snapshot
├── backend/
│   ├── config/              Django settings, ASGI entry point, URL routing
│   ├── core/
│   │   ├── services/        The one service layer: search, scoring, profiles, listings, consent
│   │   ├── engine/          Query parser, hybrid retriever, scorer, reranker, explainer
│   │   ├── ingestion/       Extraction, normalisation, embedding, verification
│   │   ├── models/          Django models mapping to DATABASE.md
│   │   └── permissions/     Role and scope checks, called only from services
│   ├── api/                 REST views under /v1 (thin; call services only)
│   ├── mcp_server/          FastMCP tools, resources and prompts (thin; call services only)
│   ├── workers/             Celery tasks: extraction, embedding, verification, reindex
│   └── tests/               Unit, integration and scoring-regression tests
└── infra/                   Render blueprint (render.yaml) and environment templates
```

## Web front end

The web app is a React single-page app at the repository root. It lists opportunities with filters for search, country, work mode and eligibility. Each card links to the employer's original posting.

Prerequisites: Node.js 20.19 or newer (22 recommended) and pnpm 12.

```bash
pnpm install          # uses the committed pnpm-lock.yaml
pnpm dev              # http://localhost:5173
pnpm test             # filter and sort logic
pnpm typecheck
pnpm build            # outputs dist/
pnpm preview          # serves dist/ at http://localhost:4173
```

The app reads `public/data/opportunities.json`. This is a snapshot of public Greenhouse job board data (copied from `backend/demo/`). Once the REST API exists, change `DATA_URL` in `src/App.tsx` to the `/v1` endpoint and the components do not need to change.

Deployment: `infra/render.yaml` defines a Render static site that runs `pnpm build` and publishes `dist/`, with security headers set.

## Local setup

The steps below are the target setup for when the Django project and Postgres store exist. Until then, use [Running tests](#running-tests), which needs nothing else.

Prerequisites: Python 3.12, Docker (for Postgres with pgvector), and Redis.

```bash
# 1. Start Postgres with pgvector and Redis
docker run -d --name ypp-db -p 5432:5432 \
  -e POSTGRES_USER=ypp -e POSTGRES_PASSWORD=ypp -e POSTGRES_DB=ypp \
  pgvector/pgvector:pg16
docker run -d --name ypp-redis -p 6379:6379 redis:7

# 2. Create the environment
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env   # run from backend/, then edit values

# 4. Migrate and run
python manage.py migrate
python manage.py runserver

# 5. In separate terminals
celery -A config worker -l info
celery -A config beat -l info
```

The MCP endpoint is served by the same web process at `/mcp`.

## Configuration

Settings come from environment variables. Secrets never go in the repository.

| Variable | Purpose | Example |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django signing key | (random, 50+ characters) |
| `DJANGO_DEBUG` | Debug mode, off in production | `false` |
| `DJANGO_ALLOWED_HOSTS` | Allowed host names | `api.example.org` |
| `DATABASE_URL` | Postgres connection string | `postgresql://ypp:...@host:5432/ypp` |
| `REDIS_URL` | Broker and cache | `redis://host:6379/0` |
| `AWS_REGION` | Bedrock and S3 region | `us-east-1` |
| `BEDROCK_EMBED_MODEL_ID` | Embedding model | `amazon.titan-embed-text-v2:0` |
| `BEDROCK_LLM_MODEL_ID` | Extraction and explanation model | (set per environment) |
| `STORAGE_BUCKET` | Object storage bucket for uploads | `ypp-uploads` |
| `EMBEDDING_DIM` | Vector size, must match the model and DB | `1024` |
| `MATCH_MIN_SCORE_DEFAULT` | Default minimum score for search | `40` |
| `SKILL_MATCH_THRESHOLD` | Embedding similarity for normalisation | `0.80` |
| `RRF_K` | Reciprocal rank fusion constant | `60` |

## Running tests

The current tests need no database, Redis or AWS credentials.

```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Test layout: `tests/test_scoring.py` (scoring model, including the worked example in TECHNICAL.md §6.7), `tests/test_engine.py` (filters, parser, RRF, rerank validation and grounding, RAG pipeline), `tests/test_services.py` (permissions, consent, audit), `tests/test_mcp.py` (a live HTTP MCP server called through the official client).

The `mcp` package is pinned to the 1.x line, which provides the `FastMCP` import used in the design. Version 2 renamed it.

## Contributing rules

1. All permission checks live in `core/services`. REST and MCP views must not implement their own checks.
2. Scoring weights and bands change only with a versioned update to `TECHNICAL.md` and the scoring regression suite.
3. Schema changes go through migrations and are recorded in `DATABASE.md`.
4. Profile text is untrusted data. It is never placed in a system prompt.
5. Do not add national ID numbers, names, gender, age, photos or school names to any scoring feature.

## Licence

See [LICENSE](LICENSE).
