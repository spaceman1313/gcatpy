# gcatpy

Python library that loads Jonathan McDowell's General Catalog of Artificial
Space Objects (GCAT) into a documented, relational, in-memory data model.

Instructions for AI coding agents working in this repository. Tool-specific
configuration lives alongside it (for Claude Code, `.claude/`).

## Verify changes

- While working: after changing a module, run only its tests, e.g.
  `uv run pytest tests/test_parser.py`, plus `uv run pyright <file>`.
- Before reporting a task done: ask whether to run the full check now.
  If yes, run it; all must pass. If no, report the task as
  "done, unverified" and list the checks that were skipped.
  - `uv run ruff format --check .`
  - `uv run ruff check .`
  - `uv run pyright`
  - `uv run pytest -m "not slow"`
  - `npx cspell --no-progress .` (rules in `cspell.json`; add real
    terms to `.cspell/project-words.txt`, never silence a typo)
- Never run tests marked `slow` unless asked.

## Authoritative sources

- GCAT format docs: https://planet4589.org/space/gcat/ . Never guess the
  format; check the docs or ask.
- Architecture decisions: `docs/adr/`. Read the relevant ADR before acting
  on its subject. Accepted ADRs are frozen: supersede them with a new
  ADR. For typo or broken-link fixes, suggest the edit; the user applies it.
- Schema and parsing design: `docs/data-model.md`, `docs/parsing.md`. Read
  them before schema or parser work. If they conflict with this file, ask.

## Hard rules

- Importing the package never touches the network. Downloads happen only on
  explicit user call. Loading reads the cache only and raises with download
  instructions if empty. Tests never hit the network.
- `-` is null. Capture each file's header update date as dataset version
  metadata.
- Vague dates: store raw string, parsed timestamp, and precision field.
  Never silently coerce to datetime.
- pandas with PyArrow-backed dtypes. No reliance on the index, no
  `inplace=True`. Backend-specific code stays behind the internal backend
  layer (planned Polars migration).
- Pandera for schema validation. Referential integrity policy:
  `strict` | `warn` (default) | `report`.
- Python 3.13 minimum. Full type hints (pyright standard). Google-style
  docstrings on every module, class, method, and function. Line length 88.
- Test fixtures are GCAT data under CC BY 4.0; keep the McDowell citation
  alongside them.

## Workflow

- Ask before major design decisions. For schema, parser, and public API
  changes, propose a plan and wait for approval before editing.
- Commits and branches follow ADR 0002 (Conventional Commits, 72-column
  header and body, `Refs #N` footers, `<type>/<desc>` branches).
- Commit at logical boundaries, not after each edit. While changes are
  still under discussion, leave them uncommitted.
- Commits you write end with an `Assisted-by: <agent>:<model_version>`
  trailer, e.g. `Assisted-by: Claude:claude-opus-5-5` (ADR 0002). Never add
  a `Co-Authored-By:` trailer naming yourself. PR descriptions carry no
  attribution line.
- Record significant decisions as a new ADR from `docs/adr/template.md`.
