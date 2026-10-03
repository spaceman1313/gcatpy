# gcatpy

<!-- Badge order: status, health, distribution, legal, tooling.
     Status leads while nothing is released. After the first PyPI release,
     drop the status badge (CI then leads), enable the PyPI badges below,
     and delete the static Python badge so the version lives in one place. -->
[![Status: pre-alpha](https://img.shields.io/badge/status-pre--alpha-orange)](#project-status)
[![CI](https://github.com/Spaceman1313/gcatpy/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Spaceman1313/gcatpy/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Code license: MIT](https://img.shields.io/badge/code%20license-MIT-green)](LICENSE)
[![Data license: CC BY 4.0](https://img.shields.io/badge/data%20license-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-fe5196?logo=conventionalcommits&logoColor=white)](https://www.conventionalcommits.org/en/v1.0.0/)

<!-- Enable after the first PyPI release:
[![PyPI](https://img.shields.io/pypi/v/gcatpy)](https://pypi.org/project/gcatpy/)
[![Python versions](https://img.shields.io/pypi/pyversions/gcatpy)](https://pypi.org/project/gcatpy/)
-->

A Python library that loads Jonathan McDowell's
[General Catalog of Artificial Space Objects (GCAT)](https://planet4589.org/space/gcat/)
into a documented, relational, in-memory data model for analysis, plotting,
and export.

## Table of contents

- [Project status](#project-status)
- [Features](#features)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Data source and attribution](#data-source-and-attribution)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## Project status

**Pre-alpha. Under active development.** The API is not yet defined and
nothing has been released. Expect breaking changes.

## Features

Planned:

- Parses the GCAT TSV files, including header metadata and the dataset
  update date, which is exposed as version information.
- Preserves McDowell's vague dates: each date field keeps the raw string,
  a parsed timestamp, and a precision indicator. Vague dates are never
  silently coerced.
- Documented tables with primary and foreign keys, plus an ER diagram.
- Referential-integrity validation with a configurable policy
  (`strict`, `warn`, or `report`).
- pandas DataFrames with PyArrow-backed dtypes, validated with Pandera.
- Offline by design: importing the package never touches the network.
  Data is downloaded to a local cache only on explicit request.

## Installation

Not yet published. Once released:

```bash
pip install gcatpy
```

Development setup (requires [uv](https://docs.astral.sh/uv/)):

```bash
git clone https://github.com/Spaceman1313/gcatpy.git
cd gcatpy
uv sync
```

## Quick start

_To be written once the public API stabilizes._

## Data source and attribution

gcatpy is a loader; it does not own the data. GCAT is compiled and
maintained by Jonathan McDowell and licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

If you use GCAT data, cite it as:

> McDowell, J., 2020: General Catalog of Artificial Space Objects,
> https://planet4589.org/space/gcat

The small subset of GCAT data committed under the test fixtures is
redistributed under the same license and attribution.

## Documentation

_Coming soon._ Design decisions are recorded as ADRs in
[`docs/adr/`](docs/adr/).

## Contributing

Contribution guidelines are in progress. In the meantime, commits follow
[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
as described in [ADR 0002](docs/adr/0002-commit-and-branch-conventions.md). AI coding agents should read
[`AGENTS.md`](AGENTS.md).

## License

Code: [MIT](LICENSE). GCAT data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
© Jonathan McDowell. See [NOTICE](NOTICE) for the full third-party terms.
