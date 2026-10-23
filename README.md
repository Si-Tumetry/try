# Youth Yellow Pages

A verified talent and opportunity directory for young people, small businesses, employers and opportunities across **Nigeria, South Africa, Kenya and Ghana**.

The platform has one search and scoring engine that is reachable through three doors:

- a web and mobile app (Next.js and Flutter, built later),
- a REST API under `/v1`,
- an MCP server at `/mcp` so AI agents can query the directory through typed tools.

Ranking uses retrieval-augmented generation (RAG) and a documented skill-scoring model. Every score comes with a breakdown and evidence links, so employers see why a candidate ranked where they did.

Success is measured by **verified paid placements and six-month retention**, not by listings or sign-ups.

## Status

This repository currently contains design documentation only. Backend and database implementation follow these documents.

| Document | Purpose |
|---|---|
| [README.md](README.md) | Overview, repository layout, local setup, configuration |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, components, deployment on Render, request flows, decisions |
| [TECHNICAL.md](TECHNICAL.md) | Implementation detail: services, ingestion and RAG pipelines, scoring, workers |
| [DATABASE.md](DATABASE.md) | Schema, indexes, constraints, retention, migrations |
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

## Local setup

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
cp ../infra/env.example .env   # then edit values

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

```bash
cd backend
pytest -q
pytest tests/scoring -q     # scoring regression suite, must pass before any weight change
```

## Contributing rules

1. All permission checks live in `core/services`. REST and MCP views must not implement their own checks.
2. Scoring weights and bands change only with a versioned update to `TECHNICAL.md` and the scoring regression suite.
3. Schema changes go through migrations and are recorded in `DATABASE.md`.
4. Profile text is untrusted data. It is never placed in a system prompt.
5. Do not add national ID numbers, names, gender, age, photos or school names to any scoring feature.

## Licence

See [LICENSE](LICENSE).
