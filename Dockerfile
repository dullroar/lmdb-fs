FROM ghcr.io/astral-sh/uv:0.11.7 AS uv
FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates fuse3 gcc git libc6-dev libfuse3-dev pkg-config python3-dev python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never

RUN useradd --create-home --shell /bin/bash tester \
    && install -d -o tester -g tester /work
WORKDIR /work
COPY --chown=tester:tester . .
USER tester
# The build context has no Git metadata. Make a local commit so the secret scan reads tracked files only.
RUN git init -q \
    && git add -A \
    && git -c user.name=build -c user.email=build@example.invalid commit -q -m "build context"
RUN uv sync --locked
# Prepare the shim cache here. The build has network. The test runs have none.
RUN python3 scripts/check_context.py
