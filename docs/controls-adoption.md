---
gist: "Read me when: you change the pinned deterministic-controls library, the check shim, controls.toml or the controls CI job, or a control check fails."
---

# Controls adoption

This repository runs the pinned `deterministic-controls` library. The adoption is advisory. The `controls` CI job is not a required check yet.

## How it works

- `scripts/check_context.py` is a shim. It runs the library `check` command with the `ci` profile.
- `scripts/controls-requirements.txt` holds the pin: one install line with a full commit. The shim reads the commit from this file.
- The shim runs the library from a cached virtual environment. The cache path is `$XDG_CACHE_HOME/deterministic-controls/<commit>/`. The default is `~/.cache/deterministic-controls/<commit>/`.
- The first run for a commit needs the network. It builds the cache. Later runs need no network.
- The shim keeps the old output lines (`ok  <script>` or `FAIL <script>`) and the exit codes `0` and `1`.
- If the library cannot run, the shim exits `2`. It never passes without a result. It never falls back to the old scripts.
- `controls.toml` selects the enabled checks.
- The old check scripts stay in `scripts/`.

## How the adoption was made

1. Audit. Step `a01-audit` wrote `docs/controls-audit.json` with a read-only audit.
2. Plan. `adopt plan --commit <pin>` showed the dry run. It listed the changes to the workflow, the shim, the pin and `controls.toml`.
3. Apply. `adopt apply --commit <pin>` wrote the files. It did not write this document. This document was written by hand.

## Where the tools did not fit

- `adopt apply` does not make a commit. The step made the commit by hand.
- `adopt apply` also rewrote `scripts/install_hooks.sh` (a `secretguard.path` fallback). That file is outside the `touches` of this step. The step restored it from the earlier commit.
- Docker. Both Docker runs have no network, but the shim needs the network once for the pinned commit. The Dockerfile now does three things:
  - It installs `git` and `python3-venv` as root. The shim setup needs `venv`. `tests/test_secret_guard.py` needs `git`.
  - It makes a local Git commit of the copied files, before `uv sync --locked`. The build context has no Git metadata. Without a repository, the secret scan reads every file, including `.venv`.
  - After `uv sync --locked`, it runs `python3 scripts/check_context.py` as `tester`. This builds the shim cache in the image, while the build has network. The core run then finds the cache.
- `.dockerignore` lists the files that enter the build context. It does not list `controls.toml`. So `controls.toml` is not in the image. The shim in the image then runs the library with its default configuration for the `ci` profile. `.dockerignore` is outside the `touches` of this step. A later step or the operator must add `!controls.toml` to `.dockerignore`.
- The session of this step could not run Docker. The driver runs `bash scripts/test_docker.sh`.

## Probes

Run date (UTC): 2026-11-24. Each probe ran in a throwaway clone of `HEAD` under `.probe/`. The command was `python3 -m deterministic_controls check --root <copy> --profile ci --format json`. The real tree was not changed. The token of the secret probe was built at run time and committed only in the clone.

| Probe | Expected rule ID | Exit code | Result |
| --- | --- | --- | --- |
| Broken relative link in a Markdown file | `markdown.local-links` | 1 | Failed with `markdown.local-links.missing-file`. |
| Stale generated index (a script changed, index not rebuilt) | `context.index-freshness` | 1 | Failed with `context.index-freshness.stale`. |
| Plan step without `gate` | `plans.schema` | 1 | Failed with `plans.schema.missing-gate`. |
| Synthetic token in a committed Markdown file | `security.secrets` | 1 | Failed with `security.secrets.github-token`. `security.personal-data` also failed with `security.personal-data.token`. |
| Tracked `driver.out` file | `repo.forbidden-artifacts` | 1 | Failed with `repo.forbidden-artifacts.tracked`. |
| Internal error (a Markdown file with mode `000`) | none: the check must not pass | 3 | Status `error`. Two checks reported a `PermissionError`. The run did not pass. |
| Clean clone, and the unreadable file restored | none | 0 | All seven checks passed. |

The shim `python3 scripts/check_context.py` ran in the clone with the bad plan step. It exited `1`. It printed `FAIL check_plan.py`. This is the old output format.

## Rollback

Run date (UTC): 2026-11-24. There is no earlier pin. Use the pre-adoption scripts to roll back.

Test result:

- The base commit is the parent of the `adopt apply` commit. A clean clone at that commit ran its own `python3 scripts/check_context.py`. It passed (exit `0`).
- A clean clone of `HEAD` ran the new shim. It passed (exit `0`).

Files of the adoption (from the diff between the base commit and `HEAD`):

- Added: `controls.toml`, `scripts/controls-requirements.txt`, `docs/controls-adoption.md`.
- Changed: `scripts/check_context.py` (now the shim), `.github/workflows/context.yml` (new `controls` job), `Dockerfile`, `AGENTS.md`, `scripts/AGENTS.md`, `docs/README.md`.
- Kept: the old check scripts in `scripts/`, `scripts/test_docker.sh`, the CI jobs `check` and `docker`, and the `tools/` entry points.

Steps to roll back:

1. Create a new branch.
2. Either change the pin in `scripts/controls-requirements.txt` to another commit, or run `git revert` on the adoption commits.
3. For a full revert, restore the changed files from the base commit and delete the added files.
4. Run `python3 scripts/check_context.py`. It must pass.

The cache under `$XDG_CACHE_HOME/deterministic-controls/<commit>/` is safe to delete. The shim builds it again when it needs it.

## Receipt

Run date (UTC): 2026-11-24. The command ran in a clean clone of `HEAD` under `.probe/`:

`python3 -m deterministic_controls adopt receipt --root <clean clone> --commit 3a2e9f3d95136958c54f73c831e84b971fc9a054`

```json
{
  "base_revision": "f7ac7b4b3938b3799744a7717919dbb80aefac97",
  "checks_run": [
    {"check_id": "context.index-freshness", "status": "passed"},
    {"check_id": "markdown.local-links", "status": "passed"},
    {"check_id": "plans.graph", "status": "passed"},
    {"check_id": "plans.schema", "status": "passed"},
    {"check_id": "repo.forbidden-artifacts", "status": "passed"},
    {"check_id": "security.personal-data", "status": "passed"},
    {"check_id": "security.secrets", "status": "passed"}
  ],
  "commands_kept": [
    "scripts/build_context_indexes.py",
    "scripts/build_indexes.py",
    "scripts/check_links.py",
    "scripts/check_plan.py",
    "scripts/ctx_common.py",
    "scripts/scan_context_secrets.py",
    "scripts/scan_secrets.py",
    "scripts/test_docker.sh",
    "test: python3 -m unittest discover -s tests",
    "test: docker build (Dockerfile)",
    "ci-job: check",
    "ci-job: docker"
  ],
  "control_pin": "3a2e9f3d95136958c54f73c831e84b971fc9a054",
  "date": "2026-11-24",
  "enabled_checks": [
    "context.index-freshness",
    "markdown.local-links",
    "plans.graph",
    "plans.schema",
    "repo.forbidden-artifacts",
    "security.personal-data",
    "security.secrets"
  ],
  "enforcement_state": "advisory",
  "files_added": [],
  "files_changed": [],
  "profile": "ci",
  "repository": "copy",
  "schema_version": 1
}
```

Notes:

- The `rollback` list of the receipt is left out here. The Rollback section above has the steps.
- `repository` is the name of the temporary clone. It is not the name of the project.
- `files_added` and `files_changed` are empty in a clean clone. This is a known defect of the library. The Rollback section lists the files of the adoption.
- `enforcement_state` is `advisory`. The `controls` CI job is not a required check yet.

## Secret guard exceptions

none
