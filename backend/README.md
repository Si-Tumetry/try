# NextStep backend: developer setup

This is the technical guide for the backend: the matching engine, the service layer, the MCP tools, the job-board connector, and the REST API under development. For what the product is and why, read the [main README](../README.md).

## What runs today

The engine, the service layer, the MCP tools, the skills taxonomy, the Greenhouse connector, the demo loader, cursor pagination, settings, and the local embedding adapter all run without a database, Redis, or a message broker.

Not built yet: the Postgres store and migrations, Celery workers, the Django project, the write tools (`create_listing`, `record_outcome`), an LLM provider, and OAuth. The REST API in `api/` is a development server with in-memory data. Profiles and sessions reset on restart.

## Technology

| Concern | Choice |
|---|---|
| Language | Python 3.12 |
| Web framework | Starlette ASGI today. Django 5.2 LTS with Django REST Framework is planned |
| MCP server | Python MCP SDK (`mcp`, FastMCP 1.x), streamable HTTP |
| Database | PostgreSQL 16 on Render, with `pgvector` and `pg_trgm` (planned) |
| Cache and broker | Redis-compatible Render Key Value (planned) |
| Background jobs | Celery 5 with Celery Beat (planned) |
| Attachments | Stored in Postgres, at most 5 MB each (planned for certificates; CVs are read and discarded) |
| Models | Embeddings: self-hosted BAAI/bge-m3 (MIT licence, 1024 dimensions). No LLM provider yet |
| Hosting | Render: web, worker, beat, Postgres and Key Value (planned) |

## Prerequisites

- Python 3.12 or newer. Development has used 3.14 and 3.12.
- Git.
- For embeddings only: about 2.5 GB of disk for the model weights, about 2.5 GB of free RAM while the model runs, and network access once to download the model.

## 1. Create the environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

The `mcp` package is pinned to the 1.x line on purpose. Version 2 renamed `FastMCP`, which the design uses.

## 2. Configure

```bash
cp .env.example .env
```

Every variable has a default except `YPP_INGEST_CONTACT`, which is needed only to refresh the demo data. The refresh script reads `.env`, and real environment variables take precedence over it. `.env` is git-ignored, so keep secrets there and nowhere else. `.env.example` marks each variable as `used` (read by the code today) or `plan` (for a component not yet built).

## 3. Check the install

```bash
pytest -q
```

Expected: all tests pass, and one is skipped. The skipped test loads the real embedding model and runs only when you enable it (step 4).

Check that the skills taxonomy loads:

```bash
python -c "from core.taxonomy import load_taxonomy; print(len(load_taxonomy()), 'skills')"
```

Expected: `303 skills`. The loader rejects a malformed taxonomy and names the problem.

## 4. Embeddings (optional, recommended)

Embeddings use BAAI/bge-m3, which runs on the CPU. It produces 1024-dimension vectors, matching `EMBEDDING_DIM=1024`. Search works without it, using keywords only, and so do the tests and the demo.

Install torch from the CPU index first, because the default wheel pulls in GPU libraries the project does not use:

```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch
pip install -r requirements-embeddings.txt
```

Check it. This downloads the model once, about 2.2 GB, into the Hugging Face cache:

```bash
YPP_TEST_REAL_MODEL=1 pytest tests/test_embeddings.py -q
```

Expected: the test passes. It checks that the model produces 1024 dimensions and ranks related text above unrelated text.

Measured on the development machine (8 CPU cores, 7 GB RAM, no GPU):

| Measure | Result |
|---|---|
| Model load, from the local cache | about 26 seconds |
| Embedding one sentence | about 1.6 seconds, including warm-up |
| Peak memory | about 2.0 GB |

These are one machine's numbers. Measure on staging before choosing the Render worker plan.

If you load the model in a script rather than under pytest, the process can take a long time to exit after the work is done. End the script with `os._exit(0)` to skip shutdown.

To turn embeddings off, set `EMBEDDING_PROVIDER=none`. Search then uses keywords only, and the response reports `embedding_status = not_configured`.

If `EMBEDDING_DIM` does not match the model's output, the first embedding call fails with `EmbeddingDimensionMismatch`. This is deliberate: a dimension mismatch is a configuration error, and it is never hidden.

## 5. Refresh the demo data (optional)

The demo data is a snapshot of 272 public job postings from six Greenhouse boards, in `demo/greenhouse_snapshot.json`. Each posting links to the employer's own page. To refresh it, you need network access and a real contact address, which is sent to the job boards in the User-Agent header:

```bash
# set YPP_INGEST_CONTACT in backend/.env first
python -m demo.refresh_greenhouse_snapshot
```

The refresh makes one request every 5 seconds, so it takes about a minute.

## 6. Run the REST API (development only)

```bash
uvicorn api.asgi:app --reload
```

This serves `/v1` on port 8000 with in-memory demo data. Nothing is saved between restarts. The web app's dev server proxies `/v1` to this address.

## 7. The MCP tools

The six read tools are built and tested. There is no standalone MCP server yet. The tests start a live MCP server on a local port and call it through the official client, which is the best way to exercise the endpoint today.

## Configuration

Settings come from environment variables. The demo refresh script also reads `backend/.env`. Other entry points will read it once they are built, so until then, export the variables or use the refresh script.

| Variable | Purpose | Default | Status |
|---|---|---|---|
| `APP_ENV` | `dev`, `demo`, `staging` or `production`. Demo data loads only in `dev` and `demo` | `dev` | used |
| `YPP_INGEST_CONTACT` | Contact address sent to job boards. Required for live fetches | (none) | used |
| `MATCH_MIN_SCORE_DEFAULT` | Default minimum score for search (PDF section 7) | `40` | used |
| `RRF_K` | Reciprocal rank fusion constant | `60` | used |
| `EMBEDDING_DIM` | Vector size. Must match the model | `1024` | used |
| `EMBEDDING_PROVIDER` | `local` (self-hosted model) or `none` | `local` | used |
| `EMBEDDING_MODEL` | Embedding model name | `BAAI/bge-m3` | used |
| `LLM_PROVIDER` | Only `none` is accepted until a provider is chosen | `none` | used |
| `LLM_MODEL` | Model name, once a provider is chosen | (empty) | plan |
| `DATABASE_URL` | Postgres connection string | (none) | plan |
| `REDIS_URL` | Broker and cache | (none) | plan |
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` | Django settings | (none) | plan |

## Tests

The default run needs no database, Redis, model download, model API keys, or network access.

| File | Covers |
|---|---|
| `tests/test_scoring.py` | Scoring model, including the worked example in TECHNICAL.md §6.7 |
| `tests/test_engine.py` | Filters, parser, rank fusion, rerank validation and grounding, the RAG pipeline |
| `tests/test_services.py` | Permissions, consent, audit |
| `tests/test_mcp.py` | A live HTTP MCP server called through the official client |
| `tests/test_taxonomy.py` | Taxonomy validation, what counts as job text, fairness regression on real postings |
| `tests/test_listing_skills.py` | Skill matching for listings |
| `tests/test_ingestion.py` | Location parsing, the Greenhouse connector, the demo guard, the snapshot |
| `tests/test_opportunities.py` | Opportunity scope and the in-country default |
| `tests/test_pagination.py` | Cursor pagination |
| `tests/test_settings.py` | Settings, `.env` reading, `.env.example` consistency |
| `tests/test_embeddings.py` | The embedding adapter with a stub model. The real-model test is opt-in (step 4) |
| `tests/test_profiles_api.py` | Profiles and the REST API |

## Repository layout (backend)

```
backend/
├── api/          REST API under /v1 (development server)
├── core/         Engine, services, scoring, ingestion, taxonomy, settings
├── mcp_server/   MCP tools and bearer-token authentication
├── taxonomy/     The skills list (skills.json)
├── demo/         Demo snapshot and the refresh script
├── tests/        Test suite
└── requirements*.txt, .env.example
```

## Contributing rules

1. All permission checks live in `core/services`. REST and MCP views must not implement their own checks.
2. Scoring weights and bands change only with a versioned update to `TECHNICAL.md` and the scoring regression suite.
3. Schema changes go through migrations and are recorded in `DATABASE.md`.
4. Profile text is untrusted data. It is never placed in a system prompt.
5. Do not add national ID numbers, names, gender, age, photos or school names to any scoring feature. Equal-opportunity text is never matched to a skill.
