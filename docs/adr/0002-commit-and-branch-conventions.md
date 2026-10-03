# ADR 0002: Commit message and branch naming conventions

- **Status:** Proposed
- **Date:** 2026-10-02
- **Deciders:** Spaceman1313

## Context

gcatpy needs a consistent commit history for three reasons:

1. Readers of `git log` should be able to tell at a glance what kind of change each
   commit makes.
2. The project uses **merge commits** for PRs, so every individual commit on a
   feature branch lands on `main` and stays in its history. Commit messages, not just
   PR titles, are therefore permanent.
3. Release notes and version numbers should eventually be derived from history
   rather than written by hand.

[Conventional Commits 1.0.0][cc] is the most widely adopted format for this. It
mandates only `feat` and `fix`. It defines breaking-change markers and leaves other
types to convention. The common extended type list comes from
[`@commitlint/config-conventional`][commitlint-cc], which derives from the
[Angular commit guidelines][angular].

No comparable standard exists for branch names. [Git Flow][gitflow] and the
[Conventional Branch][cb] proposal both exist, but neither is consistently adopted.

## Decision

### Commit messages

All commits on `main` follow Conventional Commits 1.0.0:

```text
<type>(<scope>)!: <description>

[optional body]

[optional footer(s)]
```

- The **description** is imperative and lower-case, has no trailing period, and is
  at most 72 characters for the whole header line.
- The **body** explains *why*, not *what*; the diff already shows what changed.
  Wrap it at 72 columns.
- **Breaking changes** are marked with `!` after the type or scope, *and* a
  `BREAKING CHANGE:` footer describing the migration path.
- **Issue references** go in footers, using the keyword-space-hash form described
  in [Issue linking](#issue-linking).

The 72-column limit for commit messages is deliberately narrower than the
88-column limit for code. It follows long-standing git convention
([Pope, 2008][pope]), because `git log`, `git shortlog`, and GitHub's commit views
truncate or wrap at roughly that width.

#### Allowed types

| Type       | Use for                                                 | SemVer effect |
|------------|---------------------------------------------------------|---------------|
| `feat`     | New user-facing functionality                           | minor         |
| `fix`      | Bug fix in shipped behavior                             | patch         |
| `perf`     | Performance improvement with no behavior change         | patch         |
| `refactor` | Code change that is neither a fix nor a feature         | none          |
| `docs`     | Documentation only (README, docs site, ADRs)            | none          |
| `test`     | Adding or correcting tests or test fixtures             | none          |
| `build`    | Packaging and dependencies (`pyproject.toml`, `uv.lock`)| none          |
| `ci`       | GitHub Actions workflows and CI configuration           | none          |
| `style`    | Formatting only (Ruff format, whitespace); no logic     | none          |
| `chore`    | Repository housekeeping not covered above               | none          |
| `revert`   | Reverts a previous commit; body cites the reverted SHA  | depends       |

Any type with `!` or a `BREAKING CHANGE:` footer produces a **major** bump. While the
version is `0.y.z`, breaking changes bump the minor version instead, per
[SemVer §4][semver].

The `fix` commit type and GitHub's `Fixes #N` closing keyword are unrelated. The
type classifies the change; the keyword closes an issue.

#### Scopes

Scopes are optional. When used, they must come from this list:

| Scope        | Area                                                        |
|--------------|-------------------------------------------------------------|
| `parser`     | TSV reading, header/comment handling, null and date parsing |
| `schema`     | Table definitions, dtypes, Pandera schemas                  |
| `cache`      | Local cache location, download and refresh                  |
| `validation` | Referential-integrity checks and policies                   |
| `backend`    | The internal DataFrame abstraction layer                    |
| `adr`        | Architecture decision records                               |
| `deps`       | Dependency updates (with `build`)                           |

The list is expected to grow as the package develops. New scopes are added by
amending this ADR.

#### Issue linking

GitHub closes an issue when a [closing keyword][gh-link] (`close`, `closes`,
`closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves`, `resolved`) followed by
`#N` appears in a PR description or in a commit that reaches the default branch.
A bare `#N` reference, including `Refs #N`, only creates a cross-reference.

The ` #` separator is valid for Conventional Commits footers (spec items 8–10), so
the keyword-space-hash form satisfies both. The `Keyword: #N` colon form is not
used, because GitHub's documentation does not list it.

- The **PR description** carries `Closes #N`. GitHub links the issue to the PR
  immediately and closes it on merge.
- **Commits** that do the work carry a `Refs #N` footer. This keeps the link in git
  history, independent of GitHub, without several commits each claiming to close
  the same issue.
- A commit pushed directly to `main`, with no PR, carries `Closes #N` instead,
  since nothing else would close the issue.

GitHub's default merge-commit message contains the PR number and title but not the
description, so the `Refs #N` footers are the only issue links in `git log`.

#### Examples

Each block below is one complete commit message.

**Header only.** Suitable when the change is self-explanatory and tied to no
issue:

```text
feat(parser): preserve vague dates as raw, timestamp, and precision columns
```

```text
docs(adr): record commit and branch conventions
```

```text
build(deps): bump pandera to 0.22
```

**Header, body, and issue footer.** The body explains why; the footer links the
issue:

```text
fix(cache): raise CacheEmptyError when no TSVs are present

Loading from an empty cache previously failed with a bare
FileNotFoundError that did not tell users how to download the data.

Refs #14
```

**Breaking change.** Marked with `!` in the header and explained in a
`BREAKING CHANGE:` footer:

```text
feat(schema)!: rename satcat.jcat to satcat.catalog_id

BREAKING CHANGE: the `jcat` column is now `catalog_id` in all tables.
Rename references in downstream code.
```

**PR description** for the `fix(cache)` commit above:

```markdown
Raise `CacheEmptyError` with download instructions when the cache is empty.

Closes #14
```

### Branch names

Branches use `<type>/<short-kebab-description>`, where `<type>` is drawn from the
commit type list above. An issue number may be prepended to the description.

```text
feat/vague-date-parser
fix/42-null-dash-handling
ci/python-matrix
docs/er-diagram
```

Branch names are not enforced by tooling. They exist for human orientation only.
GitHub does not link a branch to an issue from its name; only branches created
with *Create a branch* on the issue page are linked.

### Merge strategy

PRs are merged with **merge commits**. Each branch's commits are preserved on
`main`, so branches should be cleaned up before merging. Use interactive rebase to
squash fixups, so that each remaining commit is a coherent, conventionally formatted
unit of work. The merge commit itself keeps GitHub's default message.

### Enforcement

Until the open questions below are resolved, these conventions are enforced by
review only. Automated enforcement depends on the release tooling (open question 1)
and on whether a local hook framework is adopted (open question 3).

## Consequences

**Positive**

- History is scannable and filterable, for example `git log --grep '^feat'`.
- Changelogs and version bumps can be generated from history once release tooling
  is chosen.
- Breaking changes are explicit and machine-detectable.
- Issue links survive in git history independently of GitHub.

**Negative**

- Contributors must learn the format.
- Merge commits preserve every branch commit, so sloppy commits are permanent unless
  they are cleaned up before merging.
- The scope list needs maintenance as the package grows.
- Until enforcement is automated, non-conforming commits can reach `main` if review
  misses them.

## Open questions

These need decisions before the status moves to **Accepted**:

1. **Release tooling.** The options are [commitizen][commitizen] (`cz check` for
   linting, `cz bump` for versioning, and changelog generation, all configured in
   `pyproject.toml`), [python-semantic-release][psr] (fully automated releases from
   CI), or [git-cliff][git-cliff] (changelog only, with versioning done by hand).
   Deferred until the project's release workflow is clearer.
2. **Changelog file.** Should a `CHANGELOG.md` be generated and committed, or
   should only GitHub Release notes be used? Depends on question 1, since the
   tooling determines how a changelog is produced.
3. **Local enforcement.** Should a [pre-commit][pre-commit] `commit-msg` hook
   reject non-conforming messages locally? This would introduce pre-commit as a
   project tool, which would likely also run Ruff and cspell. The alternative is a
   CI check only. Partly depends on question 1, since the hook comes from the
   chosen tool.

## References

- [Conventional Commits 1.0.0][cc]
- [`@commitlint/config-conventional` type list][commitlint-cc]
- [Angular commit message guidelines][angular]
- [Semantic Versioning 2.0.0][semver]
- [Pope, T. (2008). *A Note About Git Commit Messages*][pope]
- [GitHub Docs: Linking a pull request to an issue][gh-link]
- [Git Flow (Driessen, 2010)][gitflow]
- [Conventional Branch][cb]
- [commitizen][commitizen]
- [pre-commit][pre-commit]
- [python-semantic-release][psr]
- [git-cliff][git-cliff]

[cc]: https://www.conventionalcommits.org/en/v1.0.0/
[commitlint-cc]: https://github.com/conventional-changelog/commitlint/tree/master/%40commitlint/config-conventional
[angular]: https://github.com/angular/angular/blob/main/contributing-docs/commit-message-guidelines.md
[semver]: https://semver.org/#spec-item-4
[pope]: https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
[gh-link]: https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue
[gitflow]: https://nvie.com/posts/a-successful-git-branching-model/
[cb]: https://conventional-branch.github.io/
[commitizen]: https://commitizen-tools.github.io/commitizen/
[pre-commit]: https://pre-commit.com/
[psr]: https://python-semantic-release.readthedocs.io/
[git-cliff]: https://git-cliff.org/
