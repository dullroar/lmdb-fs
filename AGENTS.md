# Agent contract

`lmdb-fs` is a read-only FUSE filesystem built with Python, pyfuse3 and LMDB.
It projects immutable, metadata-rich objects. Each directory path is an
accumulated metadata predicate.

## Standing rules

- Before changing this repository's structure, read [repo-template](https://github.com/dullroar/repo-template) and [ralph-looper](https://github.com/dullroar/ralph-looper). Account for their layout, plan format, generated indexes, worktree rules, and validation commands in the change.
- Work on a branch. Never commit directly to `main`.
- Write in Simplified Technical English. Use short sentences, active voice and consistent terms.
- Do not commit credentials, personal data, personal paths, private host names or sensitive record-level examples. Use placeholders and aggregate evidence.
- Do not push, publish, force-push or add a remote without authorization.
- If sources conflict, use this order. Follow user instructions first, then this file, `docs/design/`, the named plan, domain documentation and references, `memory/`, implementation and tests, and historical notes.

## Load context

1. Read this file.
2. Read the short indexes in full.

   | Index | What it routes |
   | --- | --- |
   | [README.md](./README.md) | Project status, setup and commands |
   | [docs/README.md](./docs/README.md) | Design, references and guides |
   | [memory/AGENTS.md](./memory/AGENTS.md) | Findings that cost time to discover |
   | [plans/AGENTS.md](./plans/AGENTS.md) | Plan format and execution state |
   | [scripts/AGENTS.md](./scripts/AGENTS.md) | Deterministic commands for agents and CI |

3. Open only the files whose **Read when**, **Read me when** or **Run me when** line matches the task. For a large file, find the relevant headings and read those sections.
4. Stop when you know the decision, intended files, constraints and validation method.

## Context ownership

- Universal rules belong in this file. Architectural reasons belong in `docs/design/`, one premise per file.
- Fix facts where they are maintained. Keep execution state in plans and deterministic automation in scripts.
- Give each Markdown file in a generated index a `gist` in its front matter.
- Run `python3 scripts/build_indexes.py` after you change a generated index's inputs. Edit the [documents index](./docs/README.md) by hand.

## Planned work

- Work on a named plan or a task that the user explicitly identifies as off-plan. See the [plan format](./plans/AGENTS.md).
- Once the user approves the spec, proceed through the steps. Diagnose and repair failures within scope. Ask the user to decide when requirements conflict, the scope must grow, or the work needs authority that the spec does not grant.
- Protect the acceptance checks in the spec. Never weaken, skip or delete a check to get it to pass. Escalate if a protected check cannot pass as written.
- Run parallel steps only when they have no dependency and no overlap in `touches`. Run the spec's combined validation after they merge.
- A step needs recorded evidence before it is done. Report unavailable verification.
- Record rule retirement, documentation correction and acceptance of a known violation as separate outcomes. See the [specification template](./plans/for-each-plan/spec.md).

## Validation

Run the smallest check that proves the change. After any change to Markdown,
context files or scripts, run `python3 scripts/check_context.py`.
