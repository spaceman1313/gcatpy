# ADR 0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-10-02
- **Deciders:** Spaceman1313

## Context

gcatpy will accumulate design decisions that are not obvious from the code alone:
how vague dates are stored, which GCAT keys are composite, how referential
integrity is enforced, and why pandas was chosen over Polars. Without a record,
the reasoning behind these choices is lost. Future contributors, including the
original author, must then either reverse-engineer it or relitigate it.

Architecture Decision Records, as described by [Nygard (2011)][nygard], capture
each significant decision in a short, versioned document that lives alongside the
code it governs.

## Decision

The project records significant design decisions as ADRs.

### What qualifies

A decision gets an ADR when it is significant in at least one of these ways:

- **Hard to reverse.** Examples are public API shape, data model keys, and
  storage formats.
- **Constrains future work.** Examples are the DataFrame backend, the validation
  library, and the minimum Python version.
- **Likely to be questioned later.** This applies to any choice where a
  reasonable alternative was rejected.

Routine implementation choices do not need an ADR.

### Location and naming

- ADRs live in `docs/adr/`.
- Filenames follow `NNNN-short-kebab-title.md`. The number is zero-padded to four
  digits and assigned sequentially. Numbers are never reused.
- The title is a short noun phrase naming the decision, not the problem.

### Format

Each ADR uses the following sections, in this order:

1. **Header.** Title (`# ADR NNNN: <title>`), status, date, and deciders.
2. **Context.** The forces at play: requirements, constraints, and sources.
3. **Decision.** What was decided, stated in the active voice.
4. **Consequences.** Positive and negative outcomes, including trade-offs
   accepted.
5. **Open questions.** Optional, and only while the status is *Proposed*.
6. **References.** Links to GCAT documentation, library docs, PEPs, and other
   sources supporting the decision.

### Lifecycle

| Status                      | Meaning                                              |
|-----------------------------|------------------------------------------------------|
| Proposed                    | Under discussion; may be edited freely               |
| Accepted                    | In force; content is frozen                          |
| Rejected                    | Considered and declined; kept for the record         |
| Deprecated                  | No longer applicable; not replaced                   |
| Superseded by ADR NNNN      | Replaced by a later ADR                              |

Once an ADR is **Accepted**, its body is never edited except to fix typos or broken
links. A changed decision gets a **new** ADR. The old one's status changes to
*Superseded by ADR NNNN*, and the new one notes *Supersedes ADR NNNN* in its
header.

ADRs are added or changed through pull requests, so each one is reviewed
alongside the code it affects.

## Consequences

**Positive**

- Design rationale is versioned with the code and reviewed in PRs.
- New contributors can learn why the project is shaped the way it is.
- Superseded ADRs preserve the history of how thinking evolved.

**Negative**

- Writing ADRs adds overhead to significant changes.
- The "what qualifies" threshold requires judgment and will occasionally be
  applied inconsistently.

## References

- [Nygard, M. (2011). *Documenting Architecture Decisions*][nygard]
- [adr.github.io: ADR overview and templates][adr-org]
- [adr-tools][adr-tools], which originated the "Record architecture decisions"
  first ADR
- [MADR: Markdown Architectural Decision Records][madr], a heavier alternative
  template that was considered but not adopted

[nygard]: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
[adr-org]: https://adr.github.io/
[adr-tools]: https://github.com/npryce/adr-tools
[madr]: https://adr.github.io/madr/
