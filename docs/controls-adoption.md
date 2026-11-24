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

## Secret guard exceptions

none
