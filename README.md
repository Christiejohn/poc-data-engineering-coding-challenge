# Principal Data Engineer — Live Interview Repo

You've inherited this repo from a contractor. Finance is asking questions about the numbers it produces. Your job: investigate, fix, and improve.

## Setup (do this BEFORE the interview)

Required: Python 3.11+, `uv` (https://docs.astral.sh/uv/getting-started/installation/), `make`, `git`.

```bash
uv sync
make setup
```

`make setup` generates seed CSVs, builds the DuckDB warehouse, runs dbt once, and renders the ticket file (`DATA-123.md`).

## Daily commands

```bash
make run      # dbt run (incremental)
make full     # dbt run --full-refresh
make test     # dbt test
make lint     # sqlfluff lint
make sql Q="select count(*) from order_fact"   # single-shot read-only query
```

## Where things live

- `DATA-123.md` — your ticket. Read this first.
- `models/` — dbt models (orders, merchants).
- `setup/` — seed generator + SQL runner.
- `tests/` — singular dbt tests.
- `docs/designs/` — prior design docs from the team.
- `CONTRIBUTING.md` — team conventions.

## Bring your own AI tool

Claude Code, Cursor, Codex, etc. — bring whatever you're fast in.
