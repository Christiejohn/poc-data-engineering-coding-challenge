# Setup

## Prerequisites (do BEFORE the interview)

- Python 3.11 or later
- `uv` installed: https://docs.astral.sh/uv/getting-started/installation/
- `make`
- `git`

## First-time setup

```bash
uv sync
make setup
```

That builds the warehouse and renders `DATA-123.md`. Then you're ready.

## During the interview

Read `DATA-123.md` first. Useful commands:

- `make run` — incremental dbt run
- `make full` — full refresh
- `make test` — dbt tests
- `make lint` — sqlfluff
- `make sql Q="..."` — read-only single-shot query against the warehouse

## Bring your own AI

Claude Code, Cursor, Codex — bring whatever you're fast in.
