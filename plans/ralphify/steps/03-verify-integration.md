---
id: 03-verify-integration
status: pending
depends_on: [02-build-and-test]
touches:
  - plans/ralphify/steps/03-verify-integration.md
lane: none
requirements: [R3]
gate: python3 scripts/check_context.py && bash scripts/test_docker.sh && git diff --check
evidence: ""
---

# 03-verify-integration

Depends on `02-build-and-test`. Update only the step file. Rerun the context and Docker gate from the integrated worktree as the driver would. Check the template and runner links in `AGENTS.md` and the structural-change rule. Verify README commands and the existing entry points. Record the worktree base commit, exact commands, build result, test counts or concrete smoke assertions, expected opt-in skips, real FUSE result where required, and UTC date. Keep logs outside Git. Gate: `python3 scripts/check_context.py && bash scripts/test_docker.sh && git diff --check`.

The driver writes its own `evidence` field. Put detailed test evidence in the body of the verification step and commit it. The parent verifies the final child commit and result. A green build alone cannot satisfy R2 or R3.

## Repository gate

Use `uv.lock` and the existing FUSE 3 build dependencies. Run `uv run --locked pytest -m 'not integration'` and run `LMDB_FS_RUN_FUSE_TESTS=1 uv run --locked pytest -m integration` in a FUSE-capable Docker invocation. Verify reads through the real mount over its generated test corpus and require a passing test with no mount-test skip. Apply the same device-free core test and disposable mount rules as `duckdb-fs`. Preserve the `tools/` entry points and host mount instructions.

Run `git merge-base HEAD plan/ralphify` to identify the integrated base commit. Replace each pending value in the results below. For each passing check, put details after `PASS`. Include the actual Docker commands or image reference and test counts or concrete smoke results. Record `n/a` in the FUSE field for other repos. If a required test fails or skips, record that in resume notes and leave the result pending.

## Results

- Base commit: `07bc8599cb1b2306d4de63deaccbc4c998725b1d`, from
  `git merge-base HEAD plan/ralphify`.
- Commands: PASS `python3 scripts/check_context.py && bash scripts/test_docker.sh && git diff --check`.
  The context check also passed in the core container. The sandbox denied
  access to the Docker socket on the first run. The same gate passed with
  Docker daemon access.
- Docker build: PASS `lmdb-fs-test:TrnarqqL` built from the indexed source
  snapshot. The build installed the FUSE 3 dependencies and ran
  `uv sync --locked`.
- Tests: PASS `uv run --offline --locked pytest -m 'not integration'`
  passed 29 tests and deselected 1. With `LMDB_FS_RUN_FUSE_TESTS=1`,
  `uv run --offline --locked pytest -m integration` passed 1 test and
  deselected 29.
- Skips: PASS Both containers reported zero skips. The mount test is
  deselected in the core container and skips by design in an unfiltered run
  without `LMDB_FS_RUN_FUSE_TESTS=1`.
- FUSE: PASS The disposable container used `--device /dev/fuse` and
  `--cap-add SYS_ADMIN`. The test generated a 100-node corpus, built the
  index, and mounted it. It found the same files in both predicate orders,
  read a synthetic payload, observed write rejection, and unmounted.
- UTC date: 2026-11-22.

Both upstream links in `AGENTS.md` resolved to their repository READMEs.
The structural-change rule names the layout, plan format, generated indexes,
worktree rules, and validation commands. The README Docker commands match
the Dockerfile and test script. Its Ralph command uses the arguments in the
upstream runner README. The documented host mount and unmount instructions,
the `lmdb-fs` entry point, and the tracked `tools/` entry points match
the pre-migration tree.
