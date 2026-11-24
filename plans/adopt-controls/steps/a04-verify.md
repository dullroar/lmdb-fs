---
id: a04-verify
status: in_progress
depends_on: [a03-probes]
touches:
  - plans/adopt-controls/steps/a04-verify.md
lane: none
tier: light
gate: d=$(mktemp -d) && trap 'rm -rf "$d"' EXIT && git clone -q . "$d/clone" && cd "$d/clone" && python3 scripts/check_context.py && python3 scripts/build_indexes.py --check && python3 scripts/secret_guard.py --tracked && bash scripts/install_hooks.sh --self-test && python3 -m unittest discover -s tests -p 'test_secret_guard.py' && bash scripts/test_docker.sh && cd - >/dev/null && grep -q 'history-findings=[0-9]' plans/adopt-controls/steps/a04-verify.md
requirements: [R4]
claimed_by: ""
claimed_at: ""
evidence: "2026-11-24 UTC, in the worktree: `python3 scripts/secret_guard.py --history` 0 findings (exit 0); `python3 scripts/check_context.py` all checks ok (exit 0); `python3 scripts/build_indexes.py --check` exit 0; `python3 scripts/secret_guard.py --tracked` 0 findings (exit 0); `bash scripts/install_hooks.sh --self-test` ok (exit 0). Host pytest not run: the session denied `uv` (test count unavailable). Clean-clone and Docker/FUSE checks run in the gate only."
---

# Verify the full gates from a clean clone

## Change

This step changes only its own step file. Agent sessions cannot clone to a temporary directory, use `mktemp` or run Docker. The gate does that: it clones the committed `HEAD` into a temporary directory, runs every check there and runs `bash scripts/test_docker.sh` (the core tests with no device and no network, then the real FUSE mount run with zero skips). Your part:

1. In this worktree, run `python3 scripts/secret_guard.py --history`. Write its finding count on its own line under "Resume notes" as `history-findings=<count>` (`0` if none), in place of `(none)`. If the count is more than `0`, do not hide it: list the findings by rule and path (never the secret) under "Resume notes", set the status to `blocked` and stop. The owner decides.
2. Run `python3 scripts/check_context.py`, `python3 scripts/build_indexes.py --check`, `python3 scripts/secret_guard.py --tracked`, `bash scripts/install_hooks.sh --self-test` and the host tests that run without Docker: `uv run --offline --locked pytest -m 'not integration'` if the host has `uv` and the locked environment; otherwise say so. Write each command, its result, the test counts and the UTC date in `evidence`.
3. Say under "Resume notes" that the Docker and clean-clone checks ran in the gate, not in your session. Do not claim a Docker result. Commit.

The Docker gate runs the core tests (`pytest -m 'not integration'`, no device, no network) and then the real FUSE mount run. The mount run needs `/dev/fuse`. It must run `test_mounted_lmdb_fs_supports_normal_reads` with zero skips. The gate checks this. Do not claim a pass for the Docker or FUSE run.

## Do not change

- Files outside `touches`. The `gate` command. Any other file in this repository.

## Already done by earlier steps

- a03-probes: the probes, the rollback test and the receipt in `docs/controls-adoption.md`.

## Done when

- The gate passes. The evidence has the commands, the results, the counts, the date and the history count.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

After the operator merges this plan, the operator runs `bash scripts/install_hooks.sh` in the canonical clone.

## Resume notes

history-findings=0

- The clean-clone checks and the Docker and FUSE run ran in the gate, not in this session. This session reports no Docker result.
- The host pytest run (`uv run --offline --locked pytest -m 'not integration'`) did not run. The session denied the `uv` command twice. The driver gate and the Docker core run cover this test set.
