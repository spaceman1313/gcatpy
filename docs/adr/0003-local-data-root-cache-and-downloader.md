# ADR 0003: Local data root, TSV cache, and downloader

- **Status:** Proposed
- **Date:** 2026-10-03
- **Deciders:** Spaceman1313

## Context

gcatpy loads GCAT from tab-separated files published at
`https://planet4589.org/space/gcat/tsv/...` ([GCAT home][gcat]). The project
rules require that importing the package never touches the network, that
downloads happen only on explicit request, and that loading reads only local
files.

Facts about the source that shape this decision:

- GCAT publishes about 40 TSV files across `tsv/tables/`, `tsv/cat/`,
  `tsv/derived/`, `tsv/launch/`, and `tsv/worlds/` ([GCAT home][gcat]).
- Each TSV starts with `#`-prefixed header lines. The first holds the column
  names. The second holds a per-file update stamp, observed in `orgs.tsv` as
  `# Updated 2026 Oct  2 2146:37`: the day is space-padded and the time is
  written `HHMM:SS`.
- The GCAT release number appears only on the HTML index page, in a line of
  the form `GCAT Release 1.8.8 (2026 Sep 3) | Data Update 2026 Oct 2`
  ([GCAT home][gcat]). The TSVs do not carry it.
- The index page's links are not a reliable file list.
- The `tar.gz` bundles under `/data/` contain the fixed-width text format,
  not TSV. They are out of scope.

The intended users are scientists and analysts, not necessarily Python
developers. They cannot be assumed to know how to set environment variables
or where their OS hides per-user application data. Some will want to inspect
the raw TSVs directly or keep several downloads side by side for comparison.

## Decision

### 1. One local data root

All gcatpy files on the user's machine live under one **data root**:

```text
<data root>/
  .gcatpy-root          # marker file; identifies a gcatpy-created root
  config.toml           # user settings (contents TBD by later ADRs)
  cache/                # downloaded GCAT files (see section 3)
  enumerations/         # code tables, user-editable (see section 5)
  reports/              # load and download reports (format TBD)
```

The **default root** is `platformdirs.user_data_dir("gcatpy",
appauthor=False)` ([platformdirs][platformdirs]):

| OS      | Default root                              |
|---------|-------------------------------------------|
| Windows | `%LOCALAPPDATA%\gcatpy`                   |
| macOS   | `~/Library/Application Support/gcatpy`    |
| Linux   | `~/.local/share/gcatpy` (respects XDG)    |

The cache is deliberately in the data directory rather than the OS cache
directory. Users can then find the cache, settings, enumerations, and
reports in one place, laid out the same way on every OS. A side benefit is that the
cache is safe from tools that purge `~/.cache`.

Because all three defaults are hidden folders, gcatpy provides discovery
helpers:

- `gcatpy.paths()` returns and prints every resolved location.
- `gcatpy.open_data_dir()` opens the root in the OS file manager
  ([`os.startfile`][startfile] on Windows, `open` on macOS, `xdg-open` on
  Linux).

A visible default such as `~/gcatpy_data` (the approach of
[scikit-learn's `get_data_home`][sklearn]) was rejected. It clutters the
home folder and departs from platform conventions, and the helpers address
discoverability.

### 2. Choosing a different root

The root is resolved in this order. The first that applies wins.

1. A `root_dir=` argument on the public function being called (`download`,
   `load`, and others).
2. A **pointer file**, `location.toml`, in the default root. It contains
   only `root = '<absolute path>'`.
3. The default root.

`gcatpy.set_root_dir(path)` writes the pointer file, and
`gcatpy.set_root_dir(None)` deletes it. The pointer file always stays in the
default root, because it is the file that says where the relocated root is.
Pointer handling follows these rules:

- **Absolute paths only.** A relative path is resolved against the current
  directory when `set_root_dir` is called, and the absolute result is
  stored.
- **A missing target is an error.** If the pointer names a path that does
  not exist (for example, an unplugged drive), gcatpy raises an error that
  names both the pointer file and the missing path. It never silently falls
  back to the default.
- **No moving.** `set_root_dir` only writes the pointer. It never moves
  existing files, and it reports the previous root so the user can copy
  files themselves. A `move=True` option may be added later without
  breaking anything.
- **Pseudo-root.** A path the user supplies gets a `gcatpy` subfolder:
  `set_root_dir(r"D:\gcat")` uses `D:\gcat\gcatpy\`. The platform default
  is already a gcatpy-named folder and gets no extra level.
- **Read at call time.** The pointer and config files are read when a
  function needs them, never at import. Importing gcatpy performs no I/O.

Environment variables are not supported. They are hard for the intended
users to set, and they would add a third configuration channel.

Settings files use TOML and are read with stdlib [`tomllib`][tomllib].
Users change them through gcatpy functions and need not edit them by hand.
gcatpy writes them with a small internal emitter for flat tables of string
values, escaping per the [TOML basic-string rules][tomlstr]. A TOML writer
dependency such as `tomli-w` was rejected because the files are too simple
to need one. The emitter is isolated in one module, so a library can
replace it if settings ever need nested tables or non-string values.

### 3. Cache layout and file registry

```text
<data root>/cache/
  .lock                 # exclusive lock held during a download
  last_attempt.json     # outcome of the most recent download attempt
  data/                 # the live cache; replaced as a unit
    metadata.json
    tsv/tables/orgs.tsv # mirrors the URL path under /space/gcat/
    tsv/cat/satcat.tsv
    ...
  staging/              # exists only during a download
  data.old/             # exists only during the final swap
```

The set of files to download is fixed by an internal **file registry** in
the package source. It is not discovered by scraping the index page,
because the all-or-nothing rule in section 4 is only meaningful when "all"
is a known, fixed set. Adding a GCAT file therefore requires a gcatpy
release. That is acceptable, because a new file also needs a schema before
it can be loaded. The registry covers every published TSV from the start.
Whether it is a Python module or a data file shared with the table schemas
is an open question.

The cache holds a single, current copy. gcatpy does not keep dated
snapshots. Users who want snapshots use separate roots (section 6).

### 4. Download procedure

`gcatpy.download()` is the only function that accesses the network. It
performs these steps:

1. Acquire `cache/.lock`, created with `os.open(..., O_CREAT | O_EXCL)`. If
   the lock is already held, fail with a message naming the lock file.
2. Recover from any interrupted swap (see the swap rules below).
3. Create `cache/staging/`. It is inside the root, so the final renames
   stay on one filesystem and are atomic ([`os.replace`][osreplace]).
4. Fetch the GCAT index page and parse its release line. This step never
   fails the download (see "Release line" below).
5. Download every registry file into `staging/`, sequentially.
6. Validate each file: HTTP 200, non-empty, the first line is a `#` column
   header, and the `# Updated` line parses.
7. Write `staging/metadata.json`.
8. Swap `staging/` into place as `data/`.
9. Write `last_attempt.json` and release the lock.

**All or nothing.** If any of steps 5–7 fails for any file, `staging/` is
deleted and `data/` is left untouched. The live cache is always a complete
set from a single download.

**The swap.** On Windows, `os.replace` cannot overwrite a non-empty
directory, so the swap is two renames: `data → data.old`, then
`staging → data`, then `data.old` is deleted. Every access to the cache
first runs a recovery check: if `data/` is missing and `data.old/` exists,
`data.old/` is renamed back to `data/`. If a rename fails because a file is
open in another program (common on Windows, for example a TSV open in
Excel), the download fails with a message naming the folder, and the cache
is left in its previous state.

**Metadata.** `metadata.json` records:

- the GCAT release number, release date, and data-update date, as parsed
  from the index page;
- the download start and end times, in UTC;
- for each file: its registry name, URL, path relative to `data/`, the
  parsed `Updated` stamp, size in bytes, SHA-256, and the HTTP
  `Last-Modified` header if the server sent one.

All paths in metadata are relative to the root, never absolute.

**Release line.** The release information is recorded when available but
is never required. If the index page fails to download, or downloads but
its release line does not match the expected pattern, the release fields in
`metadata.json` are null and `DownloadResult` carries a warning that
includes the reason (and the unparsed line, if any). Only the registry TSVs
decide all or nothing.

**No cross-file date checks.** The per-file `Updated` stamps are recorded as
published. They are not compared with one another or with the index page's
data-update date, and a difference is neither an error nor a warning. The
per-file stamp is the version of that file. When a single dataset date is
needed for display, it is the index page's data-update date, labeled as
such.

**HTTP.** Downloads use stdlib [`urllib.request`][urllib], which honors
system proxy settings. Each request has a timeout and a small number of
retries with backoff. The `User-Agent` names gcatpy and its repository URL.
Requests are sequential, to be polite to the source server.

**Result.** `download()` returns a `DownloadResult` that holds the release
information and, for each file: status, bytes, duration, `Updated` stamp,
and any error. On failure it raises `DownloadError`, which carries the same
result. `last_attempt.json` keeps the outcome of the latest attempt, so a
failed download can still be investigated after the session ends.

### 5. Enumeration tables

Enumerations that GCAT defines only in its HTML documentation, such as
organization `Class` A/B/C/D ([GCAT organizations][orgs]), are curated by
gcatpy and shipped in the package. They are TSV files in GCAT's own style,
with a `#` column-header line and a version line, and are read by the same
reader as downloaded TSVs.

So that users can see, process, and correct them directly, gcatpy copies
them into `<data root>/enumerations/`, and the data model reads them from
there, never from the package. The folder also holds a `readme.txt` that
explains the update rule below.

- **When copies are written.** On the first public call that uses a root
  (`download`, `load`, and others; never at import), gcatpy writes any
  enumeration file that is missing, plus `readme.txt`.
- **Version stamp.** Each copied file's version line records the gcatpy
  version that wrote it.
- **Upgrade rule.** When the installed gcatpy version differs from a
  file's stamp, gcatpy renames the existing file to `<name>.prev.tsv`,
  replacing any older `.prev.tsv`, and writes the packaged version in its
  place. User edits are therefore never deleted outright, and the data
  always matches the installed gcatpy release.
- **Editing.** Users may edit any enumeration file. Edits persist until the
  next gcatpy version change. `readme.txt` states this and explains how to
  carry edits forward from the `.prev.tsv` file.
- **Disclosure.** At load, gcatpy compares each enumeration file with the
  packaged copy. The load report lists every file that differs, and any
  rename to `.prev.tsv` that happened during the call.

Two alternatives were rejected:

- **Write only if absent.** User edits are never touched, but users silently
  miss new packaged codes after an upgrade until they reset the files.
- **Overwrite on upgrade without a backup.** The `readme.txt` warns of
  this, but routine upgrades would still lose edits without a trace.

A code that appears in the data but not in an enumeration table is
reported as a warning, never an error, so new codes from GCAT never block a
load.

### 6. Multiple roots for comparison

Users can keep several independent roots, for example one per download
date, and load from each explicitly:

```python
old = gcatpy.load(root_dir=r"D:\gcat\2026-10-12")
new = gcatpy.load(root_dir=r"D:\gcat\2026-10-25")
```

To keep this reliable:

- **No module-level state.** gcatpy keeps no global loaded dataset and no
  cached resolved root. Everything a load needs travels with the object it
  returns.
- **Self-contained roots.** Nothing inside a root refers to an absolute
  path, so copying a whole root folder is a valid snapshot.
- **Per-root enumerations and config.** Each root has its own
  `enumerations/` and `config.toml`. Comparisons should check the
  enumeration disclosure in each load report before attributing
  differences to changes in GCAT.
- **Identification by metadata.** A root's data is identified by its
  `metadata.json`, never by its folder name. The documentation recommends
  ISO-style folder names (`2026-10-12`) so they sort correctly.

Tooling that compares two loaded datasets is out of scope for this ADR.

### 7. Deletion safety

gcatpy creates, renames, and deletes only the entries named in this ADR.
It deletes `cache/data/`, `cache/data.old/`, or `cache/staging/`, and
replaces files in `enumerations/`, only inside a root that contains the
`.gcatpy-root` marker. A path the user supplies can
therefore never cause gcatpy to delete anything it did not create.

### 8. Testing

- Unit tests run against a local HTTP server and never reach the network.
  They cover:
  - a successful download;
  - one file failing, which must leave the cache unchanged;
  - a malformed header;
  - an unreachable index page and a release line that cannot be parsed,
    both of which must still complete the download with a warning;
  - an interrupted swap and its recovery;
  - lock contention;
  - pointer-file resolution, including a missing target;
  - enumeration copy, upgrade rename to `.prev.tsv`, and disclosure.
- A real full download is a test marked `slow`, excluded by default
  (`-m "not slow"`) ([pytest markers][pytestmark]). It runs from a manually
  triggered CI workflow, not on every push, to avoid loading the source
  server.

## Consequences

**Positive**

- Importing and loading are network-free, and their behavior is
  deterministic for a given root.
- A failed or interrupted download never leaves a partial or mixed cache.
- Everything gcatpy writes is in one discoverable folder per root, with the
  same layout on every OS.
- Enumeration tables are visible and editable from the start, edits are
  disclosed, and an upgrade never deletes them outright.
- Comparing two snapshots needs no special support beyond `root_dir=`.

**Negative**

- A new GCAT file requires a gcatpy release before it can be downloaded.
- A download needs disk space for two full copies of the data during the
  swap.
- A download that overlaps one of McDowell's updates can capture a mix of
  old and new files, and gcatpy does not detect this. This risk is
  accepted. The per-file `Updated` stamps record what was actually
  captured. A strict cross-file check must not be added without
  superseding this ADR.
- A change to the GCAT index page can leave the release fields null until
  gcatpy ships an updated release-line parser.
- Enumeration edits do not carry over a gcatpy version change
  automatically. Only one previous generation (`.prev.tsv`) is kept, so
  edits not carried forward before a second upgrade are lost.
- The pointer file is the one gcatpy file that never moves with a
  relocated root.
- Earlier statements that the cache lives in the "per-user OS cache
  directory" are superseded by this ADR: the claude.ai project
  instructions and the `platformdirs` comment in `pyproject.toml`. Both are
  updated to refer to this ADR.

## Open questions

1. Should the file registry be a Python module, or a data file (for
   example JSON) shared with the per-table schemas?
2. What format should load and download reports use, and are they written
   to `reports/` automatically or only on request? This also determines the
   format of `last_attempt.json`.

## References

- [GCAT: General Catalog of Artificial Space Objects][gcat]
- [GCAT organizations database][orgs]
- [platformdirs API][platformdirs]
- [`os.replace`][osreplace]
- [`os.startfile`][startfile]
- [`tomllib`][tomllib]
- [TOML v1.0.0: strings][tomlstr]
- [`urllib.request`][urllib]
- [scikit-learn `get_data_home`][sklearn]
- [pytest: marking test functions][pytestmark]

[gcat]: https://planet4589.org/space/gcat/
[orgs]: https://planet4589.org/space/gcat/web/orgs/index.html
[platformdirs]: https://platformdirs.readthedocs.io/en/latest/api.html
[osreplace]: https://docs.python.org/3/library/os.html#os.replace
[startfile]: https://docs.python.org/3/library/os.html#os.startfile
[tomllib]: https://docs.python.org/3/library/tomllib.html
[tomlstr]: https://toml.io/en/v1.0.0#string
[urllib]: https://docs.python.org/3/library/urllib.request.html
[sklearn]: https://scikit-learn.org/stable/modules/generated/sklearn.datasets.get_data_home.html
[pytestmark]: https://docs.pytest.org/en/stable/how-to/mark.html
